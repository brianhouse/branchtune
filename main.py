#!/usr/bin/env python3

import time, json, math
from random import random
from collections import deque, OrderedDict
from housepy import config, log, util, animation
from housepy.xbee import XBee
from mongo import db
import signal_processing as sp

sensor_data = {}
sensor_rssi = OrderedDict()
labels = []
current_session = None
sessions = []

RANGE = 0, 1023
RANGE = 300, 723

rotation_x = 0, 0, 0, 0
rotation_y = 0, 0, 0, 0

def message_handler(response):
    # log.info(response)
    try:
        # print(response['sensor'], response['samples'], response['rssi'])
        t = util.timestamp(ms=True)        
        sensor = response['sensor']
        sample = response['samples']
        x, y, z = sample
        rms = math.sqrt(x**2 + y**2 + z**2)
        sample.append(rms)
        rssi = response['rssi']
        if current_session is not None:
            data = {'t': t, 'sensor': sensor, 'sample': sample, 'rssi': rssi, 'session': str(current_session)}
            # print(json.dumps(data, indent=4))
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

def start_session():
    print("STARTING SESSION")
    global current_session
    t = util.timestamp(ms=True)
    current_session = db.sessions.insert({'t': t})
    sessions.append([t, None])
    print("--> %s" % current_session)

def stop_session():
    print("STOPPING SESSION")
    global current_session
    t = util.timestamp(ms=True)
    start_t = db.sessions.find_one({'_id': current_session})['t']
    duration = t - start_t
    result = db.sessions.update({'_id': current_session}, {'$set': {'duration': duration}})
    sessions[-1][-1] = t
    current_session = None


def draw():
    t_now = util.timestamp(ms=True)

    # ctx.line3(0., 0., 0., .5, .5, .5)
    # ctx.line(0., 0., .5, .5)

    # draw session highlighting
    for (start_t, stop_t) in sessions:
        if stop_t is None:
            stop_t = t_now        
        if t_now - stop_t > 10.0:
            continue        
        # ctx.line((t_now - stop_t) / 10.0, .99, (t_now - start_t) / 10.0, .99, color=(1., 0., 0., .2), thickness=10.0)    
        x1 = (t_now - stop_t) / 10.0
        x2 = (t_now - start_t) / 10.0
        ctx.rect(x1, 0.0, x2 - x1, 1.0, color=(1., 0., 0., 0.25))

    # do labels
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

    # data
    for sensor in list(sensor_data):
        samples = sensor_data[sensor]
        if len(samples):
            ctx.lines([((t_now - sample[0]) / 10.0, (sample[1][0] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)], color=(1., 0., 0., 1.))
            ctx.lines([((t_now - sample[0]) / 10.0, (sample[1][1] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)], color=(0., 1., 0., 1.))
            ctx.lines([((t_now - sample[0]) / 10.0, (sample[1][2] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)], color=(0., 0., 1., 1.))
            ctx.lines([((t_now - sample[0]) / 10.0, ((sample[1][3] / 2) - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)], color=(0., 0., 0., 1.))  # hack to bring down rms to similar range


def on_mouse_press(data):
    # x, y, button, modifers = data
    stop_session() if current_session is not None else start_session()

xbee = XBee(config['device_name'], message_handler=message_handler)
ctx = animation.Context(1000, 300, background=(1., 1., 1., 1.), fullscreen=False, title="TREE", smooth=True)    
ctx.add_callback("mouse_press", on_mouse_press)
ctx.start(draw)
