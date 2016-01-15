#!/usr/bin/env python3

import pymongo, sys
from housepy import drawing, config, log
from mongo import db, ASCENDING
import signal_processing as sp

RANGE = 0, 1023
RANGE = 300, 723

def main(session_id):
    result = db.branches.find({'session': session_id}).sort([('t', ASCENDING)])
    if not result.count():
        print("NO DATA!")
        exit()

    result = list(result)
    ts = [r['t'] for r in result]
    xs = [r['sample'][0] for r in result]
    ys = [r['sample'][1] for r in result]
    zs = [r['sample'][2] for r in result]

    duration = ts[-1] - ts[0]
    SAMPLING_RATE = 50 # hz

    x_signal = (sp.resample(ts, xs, duration * SAMPLING_RATE) - RANGE[0]) / (RANGE[1] - RANGE[0])
    y_signal = (sp.resample(ts, ys, duration * SAMPLING_RATE) - RANGE[0]) / (RANGE[1] - RANGE[0])
    z_signal = (sp.resample(ts, zs, duration * SAMPLING_RATE) - RANGE[0]) / (RANGE[1] - RANGE[0])

    ctx = drawing.Context(2000, 1000)
    ctx.plot(x_signal, stroke=(1.0, 0.0, 0.0, 1.0), thickness=2.0)
    ctx.plot(y_signal, stroke=(0.0, 1.0, 0.0, 1.0), thickness=2.0)
    ctx.plot(z_signal, stroke=(0.0, 0.0, 1.0, 1.0), thickness=2.0)
    ctx.output("graphs")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[SESSION_ID]")
    else:
        main(sys.argv[1])