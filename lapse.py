#!/usr/bin/env python
"""
lapse.py

Create a time lapse movie
 Copyright 2007 Justin Azoff <justin@bouncybouncy.net>

  License:
      GPL

"""


import sys

import pygst
pygst.require('0.10')
import gst
import gobject
import time


class LapseElement(gst.Element):

    _srcpadtemplate  = gst.PadTemplate ("srcpadtemplate",
                                        gst.PAD_SRC,
                                        gst.PAD_ALWAYS,
                                        gst.caps_new_any())

    _sinkpadtemplate = gst.PadTemplate ("sinkpadtemplate",
                                        gst.PAD_SINK,
                                        gst.PAD_ALWAYS,
                                        gst.caps_new_any())

    def info(self, m):
        print m

    def __init__(self):
        gst.Element.__init__(self)
        gst.info('creating pads')
        self.srcpad  = gst.Pad(self._srcpadtemplate,  "src")
        self.sinkpad = gst.Pad(self._sinkpadtemplate, "sink")
        gst.info('adding pads to self')
        self.add_pad(self.srcpad)
        self.add_pad(self.sinkpad)

        gst.info('setting chain/event functions')
        #self.srcpad.set_chain_function(self.src_chainfunc)
        #self.srcpad.set_event_function(self.src_eventfunc)

        self.sinkpad.set_chain_function(self.sink_chainfunc)
        self.sinkpad.set_event_function(self.sink_eventfunc)


        self.time_cb = None
        self.interval = 60
        self._calc_next()

    def _calc_next(self):
        """Given the configured interval, calculate when the next
           frame should be added to the output"""
        d = self.interval
        self.next = d + int(time.time() / d)*d

    def set_property(self, name, value):
        if name == "interval":
            self.interval = value
            self._calc_next()
        elif name =="time_cb":
            self.time_cb = value

    def sink_chainfunc(self, pad, buffer):
        #self.info("%s timestamp(buffer):%d" % (pad, buffer.timestamp))

        self.time_cb and self.time_cb(time.ctime(self.next))
        if time.time() > self.next:
            self._calc_next()
            self.srcpad.push(buffer)
            self.info("pushed buffer at " + time.ctime())
        return gst.FLOW_OK

    def sink_eventfunc(self, pad, event):
        self.info("%s event:%r" % (pad, event.type))
        self.srcpad.push_event(event)
        return True

gobject.type_register(LapseElement)

class lapse:

    def __init__(self):
        pipeline  = gst.Pipeline("time lapse")
        source = gst.element_factory_make("v4lsrc",  "source")
        text   = gst.element_factory_make("cairotextoverlay")
        tee    = gst.element_factory_make("tee")

        self.caps = gst.Caps("video/x-raw-yuv, width=640,height=480")
        filter = gst.element_factory_make("capsfilter", "filter")
        filter.set_property("caps", self.caps)


        text.set_property("halign", "left")
        text.set_property("valign", "bottom")

        
        pipeline.add(source, filter, text, tee)

        #link all elements
        gst.element_link_many(source, filter, text, tee)

        self.pipeline = pipeline
        self.text = text
        self.tee  = tee
        self.outputs=[]

    def _tcb(self, txt):
        self.text.set_property("text", txt)

    def add_output(self, filename, interval):
        self.outputs.append(dict(filename=filename,interval=interval))

        enc    = gst.element_factory_make("theoraenc")
        mux    = gst.element_factory_make("oggmux")
        sink   = gst.element_factory_make("filesink")
        lapse  = LapseElement()
        lapse.set_property("interval", interval)
        lapse.set_property('time_cb', self._tcb)
        sink.set_property("location", filename)
        self.pipeline.add(lapse, enc, mux, sink)
        gst.element_link_many(self.tee, lapse, enc, mux, sink)

    def run(self):
        if not self.outputs:
            raise RuntimeError("No outputs")        

        self.bus = self.pipeline.get_bus()
        self.pipeline.set_state(gst.STATE_PLAYING)

        while 1:
            msg = self.bus.poll(gst.MESSAGE_EOS | gst.MESSAGE_ERROR, gst.SECOND)
            if msg:
                break

        self.pipeline.set_state(gst.STATE_NULL)

    def foo(self, *args):
        print args
        sleep(self.interval)

if __name__ == "__main__":
    l = lapse()
    l.add_output(filename='video.ogm',  interval=5)
    l.add_output(filename='video2.ogm', interval=60)
    l.run()

