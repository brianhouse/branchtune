#!/usr/bin/env python3

import time, json
from random import random
from collections import deque, OrderedDict
from housepy import config, log, util, animation
from housepy.xbee import XBee
from mongo import db

sensor_data = {}
sensor_rssi = OrderedDict()
labels = []
sessions = deque()
current_session = None

RANGE = 0, 1023
RANGE = 300, 723

def message_handler(response):
    # log.info(response)
    try:
        # print(response['sensor'], response['samples'], response['rssi'])
        t = util.timestamp(ms=True)
        sensor = response['sensor']
        sample = response['samples']
        rssi = response['rssi']
        if current_session is not None:
            data = {'t': t, 'sensor': sensor, 'sample': sample, 'rssi': rssi, 'session': str(current_session)}
            print(json.dumps(data, indent=4))
            db.branches.insert(data)
        if sensor not in sensor_data:
            sensor_data[sensor] = deque()
            sensor_rssi[sensor] = None
        sensor_data[sensor].appendleft((t, sample))
        sensor_rssi[sensor] = t, rssi
        if len(sensor_data[sensor]) == 1000:
            sensor_data[sensor].pop()
    except Exception as e:
        log.error(log.exc(e))
## somehow it's possible for these to come in out of order. deque() is not safe here, all kinds of race conditions.
## why does a freakout happen every second?

def start_session():
    print("STARTING SESSION")
    global current_session
    current_session = db.sessions.insert({'t': util.timestamp(ms=True)})
    print("--> %s" % current_session)

def stop_session():
    print("STOPPING SESSION")
    global current_session
    current_session = None

def draw():
    t_now = util.timestamp(ms=True)
    for s, (sensor, (t, rssi)) in enumerate(sensor_rssi.items()):
        if t_now - t > 3:
            bar = 0.01
        else:
            bar = 1.0 - (max(abs(rssi) - 25, 0) / 100)
        x = (20 + (s * 20)) / ctx.width
        ctx.line(x, .1, x, (bar * 0.9) + .1, color=(0., 0., 0., 0.5), thickness=10)
        if sensor not in labels:
            print("Adding label for sensor %s" % sensor)
            labels.append(sensor)
            ctx.label(x, .05, str(sensor), font="Monaco", size=10, width=10, center=True)
    for sensor in list(sensor_data):
        samples = sensor_data[sensor]
        if len(samples):
            ctx.lines([((t_now - sample[0]) / 10.0, (sample[1][0] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)], color=(1., 0., 0., 1.))
            ctx.lines([((t_now - sample[0]) / 10.0, (sample[1][1] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)], color=(0., 1., 0., 1.))
            ctx.lines([((t_now - sample[0]) / 10.0, (sample[1][2] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)], color=(0., 0., 1., 1.))

            # exit()
            # ctx.plot([sample[1][0] / 1023 for sample in samples], color=(1., 0., 0., 1.))
            # ctx.plot([sample[1][1] / 1023 for sample in samples], color=(0., 1., 0., 1.))
            # ctx.plot([sample[1][2] / 1023 for sample in samples], color=(0., 0., 1., 1.))
    # i = 0
    # while i < len(sessions) and sessions[i] is None:
    #     i += 1
    # if i != len(sessions):
    #     j = i
    #     while j < len(sessions) and sessions[j] is not None:
    #         j += 1
    #     ctx.line(i / ctx.width, 0.98, j / ctx.width, 0.98, color=(1., 0., 0., .25), thickness=50.0)

def on_mouse_press(data):
    # x, y, button, modifers = data
    stop_session() if current_session is not None else start_session()

xbee = XBee(config['device_name'], message_handler=message_handler)
ctx = animation.Context(1000, 300, background=(1., 1., 1., 1.), fullscreen=False, title="TREE")    
ctx.add_callback("mouse_press", on_mouse_press)
ctx.start(draw)
