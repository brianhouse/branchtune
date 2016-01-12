#!/usr/bin/env python3

import pymongo
from housepy import drawing, config, log
from mongo import db, ASCENDING
import signal_processing as sp

result = list(db.branches.find().sort([('t_utc', ASCENDING)]))
# print(list(result))

ts = [r['t_utc'] for r in result]
xs = [r['samples'][0] for r in result]
ys = [r['samples'][1] for r in result]
zs = [r['samples'][2] for r in result]

duration = ts[-1] - ts[0]
SAMPLING_RATE = 50 # hz

x_signal = sp.resample(ts, xs, duration * SAMPLING_RATE) / 1023
y_signal = sp.resample(ts, ys, duration * SAMPLING_RATE) / 1023
z_signal = sp.resample(ts, zs, duration * SAMPLING_RATE) / 1023

ctx = drawing.Context(2000, 1000)
ctx.plot(x_signal, stroke=(1.0, 0.0, 0.0, 1.0), thickness=1.0)
ctx.plot(y_signal, stroke=(0.0, 1.0, 0.0, 1.0), thickness=1.0)
ctx.plot(z_signal, stroke=(0.0, 0.0, 1.0, 1.0), thickness=1.0)
ctx.output("graphs")
