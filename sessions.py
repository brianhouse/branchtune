#!/usr/bin/env python3

import time
from mongo import db
from housepy import util

for session in db.sessions.find():
    print(session['_id'], util.dt(session['t'], tz="America/New_York"))
