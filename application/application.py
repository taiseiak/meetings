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


# GLOBALS
if __name__== "__main__":
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
    app.logger.debug("Entering index")
    '''if 'begin_date' not in flask.session: # FIXME use later?
        init_session_values()'''
    return render_template('index.html')


@app.route("create_meeting")
def create_meeting():
    app.logger.debug("Entering create_meeting")
    return render_template("create_meeting.html")


@app.route("meeting")
def join_meeting():
    app.logger.debug("Entering join_meeting")
    return render_template("join_meeting.html")


@app.route("meeting/<meeting_id>")
def show_meeting(meeting_id):
    return render_template("meeting.html")
