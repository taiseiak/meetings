"""
Flask web app connects to Google Maps and Mongo Database.

Keep a list of meetings with different open times and users.
"""

import flask
from flask import url_for, request, render_template
import uuid
import json
import logging
# Date handling
import arrow
from pymongo import MongoClient
import config
from dateutil import tz
from bson.objectid import ObjectId
# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2  # used in oauth2 flow
# Google API for services
from apiclient import discovery
from hashlib import md5

# GLOBALS
if __name__ == "__main__":
    CONFIG = config.configuration()
else:
    CONFIG = config.configuration(proxied=True)

app = flask.Flask(__name__)
app.secret_key = CONFIG.SECRET_KEY

# Mongo database
MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST,
    CONFIG.DB_PORT,
    CONFIG.DB)

dbclient = MongoClient(MONGO_CLIENT_URL)
db = dbclient[str(CONFIG.DB)]
collection = db.meetings

# Debug messages
app.debug = CONFIG.DEBUG
if CONFIG.DEBUG:
    app.logger.setLevel(logging.DEBUG)

# Google API
SCOPES = "https://www.googleapis.com/auth/calendar.readonly"
CLIENT_SECRET_FILE = CONFIG.GOOGLE_KEY_FILE
APPLICATION_NAME = "Meetings"


# PAGES


@app.route("/")
@app.route("/index")
def index():
    """Creation of the meeting home page"""
    app.logger.debug("/Entering index")
    return render_template('create_meeting.html')


@app.route("/authorize")
def authorize():
    """Authorizing the user to input the busy times of the meeting"""
    app.logger.debug("Checking credentials for Google calendar access")
    credentials = valid_credentials()
    if not credentials:
        app.logger.debug("Redirecting to authorization")
        return flask.redirect(flask.url_for('oauth2callback'))

    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    flask.g.calendars = list_calendars(gcal_service)
    return render_template('busytimes.html')


@app.route('/oauth2callback')
def oauth2callback():
    """
    The 'flow' has this one place to call back to.  We'll enter here
    more than once as steps in the flow are completed, and need to keep
    track of how far we've gotten. The first time we'll do the first
    step, the second time we'll skip the first step and do the second,
    and so on.
    """
    app.logger.debug("Entering oauth2callback")
    flow = client.flow_from_clientsecrets(
        CLIENT_SECRET_FILE,
        scope=SCOPES,
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    ## Note we are *not* redirecting above.  We are noting *where*
    ## we will redirect to, which is this function.

    ## The *second* time we enter here, it's a callback
    ## with 'code' set in the URL parameter.  If we don't
    ## see that, it must be the first time through, so we
    ## need to do step 1.
    app.logger.debug("Got flow")
    if 'code' not in flask.request.args:
        app.logger.debug("Code not in flask.request.args")
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
        ## This will redirect back here, but the second time through
        ## we'll have the 'code' parameter set
    else:
        ## It's the second time through ... we can tell because
        ## we got the 'code' argument in the URL.
        app.logger.debug("Code was in flask.request.args")
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        flask.session['credentials'] = credentials.to_json()
        ## Now I can build the service and execute the query,
        ## but for the moment I'll just log it and go back to
        ## the main screen
        app.logger.debug("Got credentials")
        return flask.redirect(flask.url_for('authorize'))


@app.route("/meeting/<meeting_id>/userlinks")
def userlinks(meeting_id):
    """Page to show the links that will be sent out to the users"""
    users = get_users(meeting_id)
    users_list = []
    for user in users:
        users_list.append({'email': user['email'],
                           'link': flask.url_for('add_busytimes',
                                                 meeting_id=meeting_id,
                                                 username=user['hash'],
                                                 _external=True)})
    flask.g.users = users_list
    flask.g.meeting_name = flask.session['meeting_name']
    flask.g.mainuser = flask.session['mainuser']
    return flask.render_template('userlinks.html')


@app.route("/initialize_meeting", methods=['POST'])
def initialize_meeting():
    """
    POST method that actually create the meeting
     and inputs things to the database
    """
    app.logger.debug(request.form)
    app.logger.debug("Initializing meeting")

    flask.session['meeting_name'] = request.form['meeting_name']
    flask.session['emails'] = []

    your_email = request.form['your_email']
    daterange = request.form['daterange']
    meeting_begin = request.form['meeting_begin']
    meeting_end = request.form['meeting_end']
    group_emails = request.form.getlist('group_emails[]')

    setrange(daterange, meeting_begin, meeting_end)

    flask.session['meeting_id'] = create_database(
        flask.session['meeting_name'], meeting_begin, meeting_end,
        flask.session['begin_date'], flask.session['end_date'], your_email,
        group_emails)

    return flask.jsonify(result=url_for("userlinks",
                                  meeting_id=flask.session['meeting_id']))


@app.route("/meeting/<meeting_id>")
def show_meeting(meeting_id):
    """Page to show the responded and free times of the meeting"""
    flask.session['meeting_id'] = meeting_id
    meeting_info = collection.find_one({"_id": ObjectId(meeting_id)})
    flask.g.meeting_name = meeting_info['meeting_name']
    flask.g.open_times = meeting_info['free_times']
    return render_template("meeting.html")


@app.route("/meeting/<meeting_id>/user/<username>")
def add_busytimes(meeting_id, username):
    """Page to redirect to either the free time meeting page or to the
    calendars page"""
    flask.session['meeting_id'] = meeting_id
    flask.session['username'] = username
    meeting = collection.find_one({"_id": ObjectId(meeting_id)})
    flask.session['end_date'] = meeting['end_date']
    flask.session['begin_date'] = meeting['begin_date']
    for user in meeting['emails']:
        if user['hash'] == username:
            if user['responded']:
                return flask.redirect(flask.url_for('show_meeting',
                                                    meeting_id=meeting_id))
            else:
                break
    return flask.redirect(flask.url_for('authorize'))


@app.route("/get_free_times")
def send_free_times():
    """Gets the free times of the meeting"""
    # has information for users as well
    free_times = get_free_times(flask.session['meeting_id'])
    return flask.jsonify(result=free_times)


@app.route("/_get_events", methods=['POST'])
def getevents():
    """Send over the events of clicked calendars."""
    app.logger.info("getting events")
    event_list = []
    free_list = get_free_times(flask.session['meeting_id'])
    end = flask.session['end_date']
    begin = flask.session["begin_date"]

    calendars = request.form.getlist('list[]')
    add_to_event_list(event_list, calendars, begin, end)
    new_free_list = calculate_free_list(event_list, free_list['free_times'])
    update_database(flask.session['meeting_id'], new_free_list)
    update_user_updated(flask.session['meeting_id'], flask.session['username'])

    return flask.jsonify(result=url_for('show_meeting',
                                        meeting_id=
                                        flask.session['meeting_id']))


# Methods

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value.
    """
    if 'credentials' not in flask.session:
        return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
            credentials.access_token_expired):
        return None
    return credentials


def get_gcal_service(credentials):
    """
    We need a Google calendar 'service' object to obtain
    list of calendars, busy times, etc.  This requires
    authorization. If authorization is already in effect,
    we'll just return with the authorization. Otherwise,
    control flow will be interrupted by authorization, and we'll
    end up redirected back to /choose *without a service object*.
    Then the second call will succeed without additional authorization.
    """
    app.logger.debug("Entering get_gcal_service")
    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http_auth)
    app.logger.debug("Returning service")
    return service


def list_calendars(service):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict.
    The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")
    calendar_list = service.calendarList().list().execute()["items"]
    result = []
    for cal in calendar_list:
        kind = cal["kind"]
        id = cal["id"]
        if "description" in cal:
            desc = cal["description"]
        else:
            desc = "(no description)"
        summary = cal["summary"]
        # Optional binary attributes with False as default
        selected = ("selected" in cal) and cal["selected"]
        primary = ("primary" in cal) and cal["primary"]

        result.append(
            {"kind": kind,
             "id": id,
             "summary": summary,
             "selected": selected,
             "primary": primary
             })
    return sorted(result, key=cal_sort_key)


def cal_sort_key(cal):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
        selected_key = " "
    else:
        selected_key = "X"
    if cal["primary"]:
        primary_key = " "
    else:
        primary_key = "X"
    return primary_key, selected_key, cal["summary"]


def setrange(daterange, meeting_begin, meeting_end):
    """Puts all the information for meeting beginning and ending for the ranges
    """
    app.logger.debug("Entering setrange")
    daterange_parts = daterange.split()
    flask.session['begin_date'] = interpret_date(daterange_parts[0])
    flask.session['end_date'] = interpret_date(daterange_parts[2])
    flask.session['meeting_begin'] = meeting_begin
    flask.session['meeting_end'] = meeting_end


def interpret_date(text):
    """Interpret the date from the daterange picker"""
    app.logger.debug("Decoding time '{}'".format(text))
    try:
        as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
            tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()


def create_database(meeting_name, meeting_begin, meeting_end, begin_date,
                    end_date, your_email, group_emails):
    """Actually inputs all the right information into the database"""
    email_list = list()
    email_list.append({'email': your_email,
                       'hash': md5(your_email.encode()).hexdigest(),
                       'responded': False})

    for email in group_emails:
        app.logger.debug("email is: {}".format(email))
        email_list.append({'email': email,
                           'hash': md5(email.encode()).hexdigest(),
                           'responded': False})

    free_times = create_free_times(begin_date, end_date, meeting_begin,
                                   meeting_end)

    insert_bson = {'meeting_name': meeting_name,
                   'meeting_begin': meeting_begin,
                   'meeting_end': meeting_end,
                   'begin_date': begin_date,
                   'end_date': end_date,
                   'emails': email_list,
                   'free_times': free_times}
    app.logger.debug(insert_bson)
    meeting_id = collection.insert_one(insert_bson).inserted_id
    flask.session['mainuser'] = flask.url_for(
        'add_busytimes', meeting_id=str(meeting_id),
        username=md5(your_email.encode()).hexdigest(),
        _external=True)
    app.logger.debug("mainuser link: {}".format(flask.session['mainuser']))

    return str(meeting_id)


def create_free_times(begin_date, end_date, meeting_begin, meeting_end):
    """Initializes all the free times from the information and returns that
    list of free times"""
    begin_date = arrow.get(begin_date)
    end_date = arrow.get(end_date)
    free_list = []

    def _to_num(time_str):
        hh, mm = map(int, time_str.split(':'))
        return [hh, mm]

    s_hr = _to_num(str(meeting_begin))[0]
    s_min = _to_num(str(meeting_begin))[1]
    e_hr = _to_num(str(meeting_end))[0]
    e_min = _to_num(str(meeting_end))[1]

    while begin_date <= end_date:
        start_date = begin_date.shift(hours=s_hr, minutes=s_min)
        stop_date = begin_date.shift(hours=e_hr, minutes=e_min)
        free_list.append(
            {'name': 'open',
             'start': start_date.isoformat(),
             'end': stop_date.isoformat()})
        begin_date = begin_date.shift(days=1)
    free_list = sorted(free_list, key=lambda k: arrow.get(k['start']))
    return free_list


def get_free_times(meeting_id):
    """Not only gets free times, but other info as well!"""
    meeting = collection.find_one({"_id": ObjectId(meeting_id)})
    result = {"free_times": meeting['free_times'], "users": meeting['emails']}
    return result


def get_users(meeting_id):
    """Gets the users of the meeting.

    The user information is the email, the hash, and the responded or not
    """
    meeting = collection.find_one({"_id": ObjectId(meeting_id)})
    return meeting['emails']


def add_to_event_list(event_list, calendars, begin, end):
    """Method to get all the events and add to the event list"""
    service = get_gcal_service(valid_credentials())
    for calen in calendars:
        try:
            eventsResult = service.events().list(
                calendarId=calen, timeMin=begin, timeMax=end,
                singleEvents=True,
                orderBy='startTime').execute()
            events = eventsResult.get('items', [])
            for event in events:
                input_event = dict()
                input_event['name'] = event['summary']
                input_event['start'] = arrow.get(
                    event['start']['dateTime'])
                input_event['end'] = arrow.get(
                    event['end']['dateTime'])
                event_list.append(input_event)
        except:
            app.logger.debug('had a bad request')


def calculate_free_list(event_list, free_list):
    """Calculates all the remaining free times from the free list and event
    list"""
    app.logger.debug(event_list)
    for item in free_list:
        item['start'] = arrow.get(item['start'])
        item['end'] = arrow.get(item['end'])
    app.logger.debug(free_list)

    for open_time in free_list:
        for busy_time in event_list:
            free_start = open_time['start'].time()
            free_end = open_time['end'].time()
            busy_start = busy_time['start'].time()
            busy_end = busy_time['end'].time()

            # check for single day events (check dates not times)
            if open_time['start'].date() == busy_time['start'].date():
                # if end times are the same, then it is an single day even
                if open_time['end'].date() == busy_time['end'].date():
                    if busy_start <= free_start:
                        if busy_end >= free_end:
                            app.logger.debug(open_time)
                            free_list.remove(open_time)
                            break
                        else:
                            # free time overlaps
                            open_time['start'] = busy_time['end']
                            continue
                    else:
                        if free_end > busy_end:
                            open_time['end'] = busy_time['start']
                            free_list.append({'name': 'open',
                                              'start': busy_time['end'],
                                              'end': open_time['end']})
                            continue
                        else:
                            if free_end <= busy_end:
                                if free_end < busy_start:
                                    open_time['end'] = busy_time['start']
                                    continue

                # Multi-day event
                elif open_time['end'].date() < busy_time['end'].date():
                    if free_start >= busy_start:
                        free_list.remove(open_time)
                        break
                    if free_end > busy_start:
                        open_time['start'] = busy_time['start']
                        continue

            # truncate the end of multi day event
            elif open_time['end'].date() == busy_time['end'].date():
                if free_start < busy_end:
                    if free_end > busy_end:
                        open_time['start'] = busy_time['end']
                        continue
                if free_end <= busy_end:
                    free_list.remove(open_time)
                    break

    for item in free_list:
        item['start'] = item['start'].isoformat()
        item['end'] = item['end'].isoformat()

    free_list = sorted(free_list, key=lambda k: arrow.get(k['start']))
    return free_list


def update_database(meeting_id, free_times):
    """Adds an updated free time list into the database"""
    collection.update_one({"_id": ObjectId(meeting_id)},
                          {'$set': {'free_times': free_times}})


def update_user_updated(meeting_id, userhash):
    """Updates the responded portion of the user information"""
    collection.update_one({'_id': ObjectId(meeting_id),
                           "emails.hash": str(userhash)},
                          {"$set": {"emails.$.responded": True}})

if __name__ == "__main__":
    app.run(port=CONFIG.PORT, host="0.0.0.0")
