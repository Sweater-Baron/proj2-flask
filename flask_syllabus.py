"""
Very simple Flask web site, with one page
displaying a course schedule.

"""

CLASS_START = "2016-01-04"

import flask
from flask import render_template
from flask import request
from flask import url_for

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we still need time
from dateutil import tz  # For interpreting local times

# Our own module
import pre  # Preprocess schedule file


###
# Globals
###
app = flask.Flask(__name__)
schedule = "static/schedule.txt"  # This should be configurable
import CONFIG


import uuid
app.secret_key = str(uuid.uuid4())
app.debug=CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)


###
# Pages
###

@app.route("/")
@app.route("/index")
@app.route("/schedule")
def index():
    app.logger.debug("Main page entry")
    if 'schedule' not in flask.session:
        app.logger.debug("Processing raw schedule file")
        raw = open('static/schedule.txt')
        flask.session['schedule'] = pre.process(raw)
        for week in flask.session['schedule']:
            do_date_stuff(week)
        

    return flask.render_template('syllabus.html')

def do_date_stuff(week_dict):
    """
    Takes a dictionary representation of a week from pre.process,
    and adds "date" and "is_now" entries.
    """
    week_start = arrow.get(CLASS_START).replace(weeks=+(int(week_dict['week']) - 1))
    # week 1 gets +0 weeks, week 2 gets +1 week, etc.
    week_dict['date'] = week_start.format("YYYY-MM-DD")
    week_dict['is_now'] = date_in_range(arrow.utcnow(), week_start.span('week'))

def date_in_range(date_object, range_object):
    """
    Determines if an arrow date object is in an arrow date range object
    (which is actually just a tuple containing the start and end dates).
    
    Note that arrow ranges can contain more than two dates, but this only
    checks between the first two in the tuple.
    """
    return (date_object >= range_object[0] and date_object < range_object[1])
    
@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] =  flask.url_for("index")
    return flask.render_template('page_not_found.html'), 404

#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"


#############
#    
# Set up to run from cgi-bin script, from
# gunicorn, or stand-alone.
#


if __name__ == "__main__":
    # Standalone, with a dynamically generated
    # secret key, accessible outside only if debugging is not on
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    if app.debug: 
        print("Accessible only on localhost")
        app.run(port=CONFIG.PORT)  # Accessible only on localhost
    else:
        print("Opening for global access on port {}".format(CONFIG.PORT))
        app.run(port=CONFIG.PORT, host="0.0.0.0")
else:
    # Running from cgi-bin or from gunicorn WSGI server, 
    # which makes the call to app.run.  Gunicorn may invoke more than
    # one instance for concurrent service. 
    app.secret_key = CONFIG.secret_key
    app.debug=False

