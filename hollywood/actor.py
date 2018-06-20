#!/usr/bin/env python

import time
import Queue
import threading
import logging
import uuid


class Base(object):


    def __init__(self):
        self.inbox = Queue.Queue()
        self.running = True
        self.uuid = str(uuid.uuid4()).split('-')[0]

    def start(self):
        raise NotImplementedError("Do not instantiate Actor class directly, use the flavours.")

    def stop(self):
        logging.debug("[%s] Received stop signal.", self.uuid)
        self.running = False

    def _loop(self):
        while self.running:
            if self.inbox.empty():
                time.sleep(0.0001)
                continue
            args, kwargs = self.inbox.get()
            self.receive(*args, **kwargs)
        logging.debug("[%s] Shutting down.", self.uuid)

    def tell(self, *args, **kwargs):
        self.inbox.put((args, kwargs))
        return self

    def ask(self, *args, **kwargs):
        queue = Queue.Queue()
        queue.put(self.receive(*args, **kwargs))
        return queue

    def receive(self, *args, **kwargs):
        raise NotImplementedError("'receive' method must be overriden.")


class Threaded(Base):


    def start(self):
        threading.Thread(target=self._loop).start()

    def ask(self, *args, **kwargs):
        queue = Queue.Queue()
        threading.Thread(target=self.future, args=(queue, args), kwargs=kwargs).start()
        return queue

    def future(self, queue, args, **kwargs):
        """
            Wraps the 'receive' method by capturing its output and returning
            it in the form of a Queue.Queue.

            You can then do 'obj.get()' to obtain the result (blocks if
            not done, check the Queue.Queue for other non-blocking options).
        """
        logging.debug("Future::%s", __name__ + "::" + self.__class__.__name__)
        queue.put(self.receive(*args, **kwargs))
