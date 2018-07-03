#!/usr/bin/env python

import threading
import Queue
import logging

import exceptions


class Threaded(object):

    def __init__(self, method, *args, **kwargs):
        self.queue = Queue.Queue()
        self.method = method
        self.args = args
        self.kwargs = kwargs
        if hasattr(method, '__self__'):
            self.name = method.__self__.__class__.__name__
        else:
            self.name = method.__name__
        self.thread = threading.Thread(name=self.name,
                                       target=self.__wrap)
        self.thread.start()

    def __wrap(self):
        """
            Wraps the 'receive' method by capturing its output and returning
            it in the form of a Queue.Queue.

            You can then do 'obj.get()' to obtain the result (blocks if
            not done, check the Queue.Queue for other non-blocking options).
        """
        logging.debug("Future::%s (%s, %s)", self.method.__name__, self.args, self.kwargs)
        try:
            result = self.method(*self.args, **self.kwargs)
        except Exception as error:
            logging.error(error, exc_info=True)
            raise hollywood.exceptions.ActorRuntimeError
        self.queue.put(result)

    def ready(self):
        return self.queue.qsize()

    def get(self, block=True, timeout=None):
        return self.queue.get(block=block, timeout=timeout)
