#!/usr/bin/env python3

# import model
import time
from random import random
from collections import deque
from housepy import config, log, util, animation
from housepy.xbee import XBee

samples = deque()

def message_handler(response):
    # log.info(response)
    try:
        global samples
        t = util.timestamp(ms=True)
        # model.insert_data(t, response['samples'], response['sensor'])
        data = [sample / 1023 for sample in response['samples']]
        # print(response['samples'])
        # data = [random(), random(), random()] 
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
