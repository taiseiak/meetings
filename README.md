# Meetings

A web application that lets users find an open time between a specific
date range and time range by linking their Google calendars.

## Author
Taisei Klasen taiseiklasen@gmail.com

## Requirements and running

This applicaiton will require the person setting up the server to have
two additional files that are not in the git repository. They are the
credentials.ini and the client_secret.json files. These will need to be
in the "application" directory. There also needs
 to be an Mlab account set up with the collection "meetings" in the
 database before the app can run. When running the app for the first time,
 the database should be empty. When running, all that is needed to do
is to call "make run".

## Credentials.ini

This file will need this information: SECRET_KEY, GOOGLE_KEY_FILE,
PORT, DB, DB_USER, DB_USER_PW, DB_HOST, DB_PORT. All should be strings,
and the google key file should be the relative path to the key optained by
the Google developer API website.

## Google key file

This file can be obtained by the the google API authentication website.

## Implementation
The server is run on Flask, and the calendar is based on Google Calendar
API. Front end uses Bootstrap, and the database is on MongoDB hosted by
MLabs.

## How it works

This webapp is stripped down to the bare-bones usefulness of finding free-times
in a meeting. For some group to effectively find a meeting time where
many people, the busy times should not be able to change after they are
input so that a common time is agreed upon as quickly and effectively as
possible. Each user to join the meeting will need a special link for the
meeting and username (their hashed email) and keep the meeting_id or link
tracked to check up on the meeting page. The link that the users got to join
the meeting works as well to check up on the meeting page. It will directly link
to the meeting page once the person has input their busy times. I kept the functionality
to a minimum so that finding free times between people is the quickest - no one
gets access to their individual free times, no one get to change busy times afterwards,
the free times are just the times when no one has events in their schedule in the
specified time frame. Effective applications get to the point the quickest, and
I believe I have done that.


There are four pages to this web application. They are split into two
categories: Creation and Joining

### Creation
![Alt text](/img/Homepage.jpg?raw=true "Homepage")

The home page is the page where the meeting will be created. There are
multiple fields to the application. NOTE: for the emails to work, enter
or tab needs to be pressed after the email has been entered. The create meeting
button will not do anything if the fields are not correctly input.

![Alt text](/img/links.jpg?raw=true "links")

After the user creates the meeting name, times, and dates, they will be directed
to a screen where the links of joining and checking up with the free times
of the meeting are shown. Here the links are mailto links, where the user just
needs to click send on their computer email application to send the links to the
users in the group. The busy times button will direct the user to their
own busy times submit link, where at this point they have the same power as
all the other users in the group: submit busy times and check up on free times.

### Joining
![Alt text](/img/busytimes.jpg?raw=true "buystimes")

The joining the meeting is simple. Enter the link into the url of the browser,
and if the user has not submit their busy times yet, they will enter the calendars
they want to submit. That is all that is required to submit the busy times. After
they have submitted their busy time calendars, they will never see this screen again.

![Alt text](/img/Freetimes.jpg?raw=true "Freetimes")


The meeting page shows the name of the meeting, the users that have responded and not
responded, and the free times. This is the only information needed to create
a meeting between people, as then people can just choose the free time they want
to create the meeting in and create the time frame on their own.