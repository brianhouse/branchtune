#!/usr/bin/env python3

import serial, threading, time, os, socket, queue
from housepy import config, log, util

"""
Consume messages as fast as they come in one thread, process them in another.
Keep track of the hz achieved for each connected device.

"""


class FeatherListener(threading.Thread):

    def __init__(self, port=23232, message_handler=None, blocking=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self.data = queue.Queue()
        FeatherHandler(self.data, message_handler)
        self.events = {}
        self.rater = Rater(self.events)        
        try:
            self.receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.receiver.bind(('', port))
        except Exception as e:
            log.error(log.exc(e))
            return
        self.start()
        if blocking:
            try:
                while True:
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                self.connection.close()
                pass      

    def run(self):
        while True:
            try:
                message, address = self.receiver.recvfrom(1024)
                if address not in self.events:
                    self.events[address] = queue.Queue()
                self.events[address].put(1)                    
                data = message.decode('utf-8').split(',')
                self.data.put({'sensor': address, 't_utc': util.timestamp(ms=True), 'data': [float(v) for v in data[:-1]], 'rssi': int(data[-1])})
            except Exception as e:
                log.error(log.exc(e))


class FeatherHandler(threading.Thread):

    def __init__(self, data, message_handler):
        super(FeatherHandler, self).__init__()        
        if message_handler is None:
            return
        self.data = data
        self.message_handler = message_handler
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                data = self.data.get()
                self.message_handler(data)
            except Exception as e:
                log.error(log.exc(e))


class Rater(threading.Thread):

    def __init__(self, events):
        super(Rater, self).__init__()
        self.daemon = True
        self.events = events
        self.start()

    def run(self):        
        start_t = time.time()
        while True:
            t = time.time()
            if t - start_t >= 1:
                for device, events in self.events.items():
                    hz = events.qsize()
                    log.info("%s: %shz" % (device, hz))
                    while hz:
                        try:
                            events.get_nowait()                  
                        except queue.Empty:
                            break
                        hz -= 1
                start_t = t
            time.sleep(0.1)


if __name__ == "__main__":
    def message_handler(response):
        log.info(response)
        pass
    fl = FeatherListener(message_handler=message_handler, blocking=True)

