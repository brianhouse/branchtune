#!/usr/bin/env python3

import pymongo, sys, subprocess, time, math, threading
from collections import deque, OrderedDict
from housepy import drawing, config, log, sound, util, osc, animation
from housepy.xbee import XBee
from mongo import db, ASCENDING
import signal_processing as sp
import numpy as np

sensor_data = {}
sensor_rssi = OrderedDict()
labels = []

RANGE = 300, 723

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
        if sensor not in sensor_data:
            sensor_data[sensor] = deque()
            sensor_rssi[sensor] = None
        sensor_data[sensor].appendleft((t, sample))
        sensor_rssi[sensor] = t, rssi
        if len(sensor_data[sensor]) == 1000:
            sensor_data[sensor].pop()
    except Exception as e:
        log.error(log.exc(e))


class Audifier(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        while True:

            time.sleep(5.0)

            log.info("Start processing...")

            try:
                result = list(sensor_data[list(sensor_data.keys())[0]])[:]
            except IndexError:
                continue

            result.reverse()

            ts = [r[0] for r in result]
            rms = [r[1][3] for r in result]
            duration = ts[-1] - ts[0]
            SAMPLING_RATE = 60 # hz
            log.info("DURATION %fs" % duration)

            signal = sp.resample(ts, rms, duration * SAMPLING_RATE)
            signal = sp.remove_shots(signal)
            signal = sp.normalize(signal)    
            signal = sp.smooth(signal, 15)

            # this number should match some lower frequency bound. ie, put this in hz.
            # the smaller the number, the more it will affect small motion
            # so this should be higher than the slowest motion we care about
            # ie, dont care about motion over 0.5hz, which is 120 samples
            trend = sp.smooth(signal, 120)  
            signal -= trend
            signal += 0.5
            atrend = sp.smooth(signal, 500)

            # see the audio processing
            # ctx = drawing.Context(2000, 750)
            # ctx.plot(signal, stroke=(0.0, 0.0, 0.0, 1.0), thickness=2.0)
            # # ctx.plot(trend, stroke=(1.0, 0.0, 0.0, 1.0), thickness=2.0)
            # # ctx.plot(atrend, stroke=(0.0, 0.0, 1.0, 1.0), thickness=2.0)
            # ctx.output("graphs")

            # let's do some autocorrelation
            auto = sp.autocorrelate(signal)
            # this should be small -- if 60hz, fastest gesture would reasonably be half of that, so 30
            peaks, valleys = sp.detect_peaks(auto, 10)
            peaks = [peak for peak in peaks[1:] if peak[1] > 0.5]
            partials = []
            for peak in peaks:    
                frequency = SAMPLING_RATE / peak[0]
                partial = frequency * 1000
                partials.append([partial, float(peak[1])])
                log.info("%d samps\t%fhz\t%f magnitude\t%f map" % (peak[0], frequency, peak[1], partial))

            print(partials)
            osc.Sender(23232).send('/partials', partials)

            log.info("--> done") # around 300ms

Audifier()


def draw():
    t_now = util.timestamp(ms=True)

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
