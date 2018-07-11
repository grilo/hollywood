#!/usr/bin/env python

import Queue


class Base(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.outqueue = Queue.Queue(maxsize=1)
        self.payload = None

    def put(self, payload):
        self.outqueue.put(payload)

    def get(self, block=True, timeout=None):
        self.payload = self.outqueue.get(block, timeout)
        return self.payload

    def get_nowait(self, block=False, timeout=0):
        return self.get(block, timeout)

    def ready(self):
        return self.outqueue.qsize()
