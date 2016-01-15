#!/usr/bin/env python3

import time
from mongo import db
from housepy import util, strings

for session in db.sessions.find():
    print("%s\t%s\t%s" % (session['_id'], util.dt(session['t'], tz="America/New_York"), strings.format_time(session['duration']) if 'duration' in session else ""))
