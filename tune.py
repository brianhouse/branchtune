#!/usr/bin/env python3

import pymongo, sys, subprocess, time
from housepy import drawing, config, log, sound, util, osc
from mongo import db, ASCENDING
import signal_processing as sp
import numpy as np
from spectrometer import spectrum

def main(session_id):
    result = db.branches.find({'session': session_id}).sort([('t', ASCENDING)])
    if not result.count():
        print("NO DATA!")
        exit()

    log.info("Start processing...")

    result = list(result)
    ts = [r['t'] for r in result]
    rms = [r['sample'][3] for r in result]
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

    audio_signal = sp.make_audio(signal)
    # spectrum(audio_signal, SAMPLING_RATE)

    # AUDIO_RATE = 11025
    # filename = "%s.wav" % util.timestamp()
    # sound.write_audio(audio_signal, filename, AUDIO_RATE)
    # subprocess.call(["open", filename])
    # log.info("AUDIO DURATION %fs" % (duration / (AUDIO_RATE / SAMPLING_RATE)))

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

    # # see the audio processing
    # ctx = drawing.Context(2000, 750)
    # ctx.plot(signal, stroke=(0.0, 0.0, 0.0, 1.0), thickness=2.0)
    # ctx.plot(trend, stroke=(1.0, 0.0, 0.0, 1.0), thickness=2.0)
    # ctx.plot(atrend, stroke=(0.0, 0.0, 1.0, 1.0), thickness=2.0)
    # ctx.output("graphs")

    # # see the autocorrelation processing
    # ctx = drawing.Context(2000, 750)
    # ctx.plot(auto, stroke=(0.0, 0.0, 0.0, 1.0), thickness=2.0)
    # for peak in peaks:
    #     x = peak[0] / len(auto)
    #     ctx.line(x, 0.0, x, peak[1], stroke=(1.0, 0.0, 0.0, 1.0))
    # ctx.output("graphs")

    log.info("--> done") # around 300ms


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[SESSION_ID]")
    else:
        main(sys.argv[1])



"""
This is a super technical way to do this.

how would you do it in just max?
yeah, unclear. 



"""        