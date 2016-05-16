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

    # ctx.translate(0, 0, -1)
    # ctx.translate(-1.5, -0.5, -1)
    ctx.translate(-1.3, -0.85, -2)    

    ctx.rotate(*rotation_x)
    ctx.rotate(*rotation_y)

    # axes
    ctx.line3D(-.25, 0, 0, .25, 0, 0, color=(1., 1., 0., 1.))
    ctx.line3D(0, -.25, 0, 0, .25, 0, color=(0., 1., 1., 1.))
    ctx.line3D(0, 0, -.25, 0, 0, .25, color=(1., 0., 1., 1.))


    # for (start_t, stop_t) in sessions:
    #     if stop_t is None:
    #         stop_t = t_now        
    #     if t_now - stop_t > 10.0:
    #         continue        
    #     # ctx.line((t_now - stop_t) / 10.0, .99, (t_now - start_t) / 10.0, .99, color=(1., 0., 0., .2), thickness=10.0)    
    #     x1 = (t_now - stop_t) / 10.0
    #     x2 = (t_now - start_t) / 10.0
    #     ctx.rect(x1, 0.0, x2 - x1, 1.0, color=(1., 0., 0., 0.25))

    # for s, (sensor, (t, rssi)) in enumerate(sensor_rssi.items()):
    #     if t_now - t > 3:
    #         bar = 0.01
    #     else:
    #         bar = 1.0 - (max(abs(rssi) - 25, 0) / 100)
    #     x = (20 + (s * 20)) / ctx.width
    #     ctx.line(x, .1, x, (bar * 0.9) + .1, color=(0., 0., 0., 0.5), thickness=10)
    #     if sensor not in labels:
    #         print("Adding label for sensor %s" % sensor)
    #         labels.append(sensor)
    #         ctx.label(x, .05, str(sensor), font="Monaco", size=10, width=10, center=True)

    colors = (0., 0., 1., 1.), (1., 0., 0., 1.), (0., 1., 0., 1.) 
    for s, sensor in enumerate(list(sensor_data)):
        samples = sensor_data[sensor]
        print(sensor, len(sensor_data[sensor]))
        if len(samples):
            x = [((t_now - sample[0]) / 10.0, (sample[1][0] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)]
            y = [((t_now - sample[0]) / 10.0, (sample[1][1] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)]
            z = [((t_now - sample[0]) / 10.0, (sample[1][2] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)]
            combo_yz = [((t_now - sample[0]) / 10.0, (sample[1][2] - RANGE[0]) / (RANGE[1] - RANGE[0]), ((sample[1][1] - RANGE[0]) / (RANGE[1] - RANGE[0])) - 0.5) for sample in list(samples)]
            ctx.lines3D(combo_yz, color=colors[s])

def on_mouse_press(data):
    x, y, button, modifers = data
    print(modifiers)
    stop_session() if current_session is not None else start_session()

def on_mouse_drag(data):
    x, y, dx, dy, button, modifers = data
    global rotation_x, rotation_y
    SCALE = -0.5
    rotation_x = (dx * SCALE) + rotation_x[0], 0, 1, 0
    rotation_y = (dy * SCALE) + rotation_y[0], 1, 0, 0


xbee = XBee(config['device_name'], message_handler=message_handler)
ctx = animation.Context(1000, 700, background=(1., 1., 1., 1.), fullscreen=False, title="TREE", smooth=True, _3d=True)    
# ctx.add_callback("mouse_press", on_mouse_press)
ctx.add_callback("mouse_drag", on_mouse_drag)
ctx.start(draw)
