#!/usr/bin/env python3

# import model
import time
from random import random
from collections import deque
from housepy import config, log, util, animation
from housepy.xbee import XBee
from mongo import db

samples = deque()

def message_handler(response):
    # log.info(response)
    try:
        global samples
        print(response['sensor'], response['samples'], response['rssi'])
        t = util.timestamp(ms=True)
        db.branches.insert({'t_utc': t, 'sensor': response['sensor'], 'samples': response['samples'], 'rssi': response['rssi']})
        data = [sample / 1023 for sample in response['samples']]
        samples.appendleft((t, data))
        if len(samples) == 1000:
            samples.pop()
    except Exception as e:
        log.error(log.exc(e))

xbee = XBee(config['device_name'], message_handler=message_handler)


ctx = animation.Context(1000, 300, background=(1., 1., 1., 1.), fullscreen=False, title="TREE")    

def draw():
    if len(samples):
        x_points = [(s / ctx.width, sample[1][0]) for (s, sample) in enumerate(list(samples))]
        y_points = [(s / ctx.width, sample[1][1]) for (s, sample) in enumerate(list(samples))]
        z_points = [(s / ctx.width, sample[1][2]) for (s, sample) in enumerate(list(samples))]
        ctx.lines(x_points, color=(1., 0., 0., 1.), thickness=0.5)    
        ctx.lines(y_points, color=(0., 1., 0., 1.), thickness=0.5)    
        ctx.lines(z_points, color=(0., 0., 1., 1.), thickness=0.5)    

ctx.start(draw)
