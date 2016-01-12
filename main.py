#!/usr/bin/env python3

import time, json
from random import random
from collections import deque
from housepy import config, log, util, animation
from housepy.xbee import XBee
from mongo import db

samples = deque()
sessions = deque()
current_session = None

def message_handler(response):
    # log.info(response)
    try:
        global samples
        # print(response['sensor'], response['samples'], response['rssi'])
        t = util.timestamp(ms=True)
        if current_session is not None:
            data = {'t': t, 'sensor': response['sensor'], 'samples': response['samples'], 'rssi': response['rssi'], 'session': str(current_session)}
            print(json.dumps(data, indent=4))
            db.branches.insert(data)
        data = [sample / 1023 for sample in response['samples']]
        samples.appendleft((t, data))
        sessions.appendleft(current_session)
        if len(samples) == 1000:
            samples.pop()
            sessions.pop()
    except Exception as e:
        log.error(log.exc(e))

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
    if len(samples):
        x_points = [(s / ctx.width, sample[1][0]) for (s, sample) in enumerate(list(samples))]
        y_points = [(s / ctx.width, sample[1][1]) for (s, sample) in enumerate(list(samples))]
        z_points = [(s / ctx.width, sample[1][2]) for (s, sample) in enumerate(list(samples))]
        ctx.lines(x_points, color=(1., 0., 0., 1.), thickness=0.5)    
        ctx.lines(y_points, color=(0., 1., 0., 1.), thickness=0.5)    
        ctx.lines(z_points, color=(0., 0., 1., 1.), thickness=0.5) 
    i = 0
    while i < len(sessions) and sessions[i] is None:
        i += 1
    if i != len(sessions):
        j = i
        while j < len(sessions) and sessions[j] is not None:
            j += 1
        ctx.line(i / ctx.width, 0.98, j / ctx.width, 0.98, color=(1., 0., 0., .25), thickness=50.0)

def on_mouse_press(data):
    # x, y, button, modifers = data
    stop_session() if current_session is not None else start_session()

xbee = XBee(config['device_name'], message_handler=message_handler)
ctx = animation.Context(1000, 300, background=(1., 1., 1., 1.), fullscreen=False, title="TREE")    
ctx.add_callback("mouse_press", on_mouse_press)
ctx.start(draw)
