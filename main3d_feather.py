#!/usr/bin/env python3

import time, json, math, socket
from random import random
from collections import deque, OrderedDict
from housepy import config, log, util, animation
from feather import FeatherListener
from mongo import db
import signal_processing as sp
import numpy as np

sensor_data = {}
sensor_rssi = OrderedDict()
labels = []
current_session = None
sessions = []

# 1G is 9.8m/s, so 2G sensitivity is +-19.6
# 4G sensitivity is +-39.2
RANGE = -40, 40

rotation_x, rotation_y = (-53.0, 0, 1, 0), (13.5, 1, 0, 0)

colors = (0., 0., 0., 1.), (0., 0., 0., 1.), (1., 0., 0., 1.), (0., 1., 0., 1.), (0., 0., 1., 1.)

def on_message(response):
    try:
        # print(response['sensor'], response['samples'], response['rssi'])
        t = util.timestamp(ms=True)
        sensor = config['sensors'][response['id']]
        sample = response['data']
        x, y, z = response['data']
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

    ctx.translate(-1., -0.85, -1.5)        

    ctx.rotate(*rotation_x)
    ctx.rotate(*rotation_y)

    colors = (1., 1., 1., 1.), (.7, 1., 1., 1.), (1., .7, .7, 1.), 
    for s, sensor in enumerate(list(sensor_data)):
        samples = sensor_data[sensor]
        if len(samples):
            # x = [((t_now - sample[0]) / 10.0, (sample[1][0] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)]
            # y = [((t_now - sample[0]) / 10.0, (sample[1][1] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)]
            # z = [((t_now - sample[0]) / 10.0, (sample[1][2] - RANGE[0]) / (RANGE[1] - RANGE[0])) for sample in list(samples)]

            ts = [(t_now - sample[0]) / 10.0 for sample in samples]
            ys = [(sample[1][2] - RANGE[0]) / (RANGE[1] - RANGE[0]) for sample in samples]
            zs = [(sample[1][1] - RANGE[0]) / (RANGE[1] - RANGE[0]) - 0.5 for sample in samples]

            # ys = list(sp.smooth(sp.remove_shots(ys)))
            # zs = list(sp.smooth(sp.remove_shots(zs)))

            # ys = list(sp.remove_shots(ys))
            # zs = list(sp.remove_shots(zs))
            ys = (np.array(ys) * 2.0) - 0.5
            zs = (np.array(zs) * 2.0) - 0.5
            ys = sp.smooth(ys, 20)
            zs = sp.smooth(zs, 20)

            # combo_yz = [((t_now - sample[0]) / 10.0, (sample[1][2] - RANGE[0]) / (RANGE[1] - RANGE[0]), ((sample[1][1] - RANGE[0]) / (RANGE[1] - RANGE[0])) - 0.5) for sample in list(samples)]
            combo_yz = [(ts[i], ys[i], zs[i]) for i in range(0, len(ys))]
            ctx.lines3D(combo_yz, color=colors[s], thickness=2.0)

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
    print(rotation_x, rotation_y)


fl = FeatherListener(message_handler=on_message)
ctx = animation.Context(1000, 700, background=(0., 0., 0., 1.), fullscreen=False, title="TREE", smooth=True, _3d=True, screen=0)    
# ctx.add_callback("mouse_press", on_mouse_press)
ctx.add_callback("mouse_drag", on_mouse_drag)
ctx.start(draw)
