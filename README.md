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