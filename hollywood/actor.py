#!/usr/bin/env python

import time
import Queue
import threading
import logging

# Clean shutdown with ctrl-c
import sys
import signal
def signal_handler(signal, frame):
        System.halt()
        sys.exit(1)
signal.signal(signal.SIGINT, signal_handler)


class System(object):

    actors = {}
    actor_lock = threading.RLock()

    @classmethod
    def register(cls, actor):
        cls.actors[actor.address] = actor

    @classmethod
    def unregister(cls, address):
        with cls.actor_lock:
            logging.debug("Halting: %s", address)
            if address in cls.actors:
                del cls.actors[address]

    @classmethod
    def halt(cls, block=True, timeout=None):
        with cls.actor_lock:
            logging.warning("Halting all actors.")
            for address in reversed(cls.actors.keys()):
                cls.actors[address].stop()
                System.unregister(address)
            logging.info("Halting completed.")


class Actor(object):

    def __init__(self):
        self.inbox = Queue.Queue()
        self.running = True
        self.address = __name__ + "/" + self.__class__.__name__
        System.register(self)
        self.start()

    def start(self):
        raise NotImplementedError("Do not instantiate Actor class directly, use the flavours.")

    def stop(self):
        logging.debug("[%s] Received stop signal.", self.address)
        self.running = False
        System.unregister(self.address)

    def _loop(self):
        while self.running:
            if self.inbox.empty():
                time.sleep(0.0001)
                continue
            args, kwargs = self.inbox.get()
            self.receive(*args, **kwargs)
        self.stop()
        logging.debug("[%s] Shutting down.", self.address)

    def tell(self, *args, **kwargs):
        self.inbox.put((args, kwargs))
        return self

    def ask(self, *args, **kwargs):
        queue = Queue.Queue()
        queue.put(self.receive(*args, **kwargs))
        return queue

    def receive(self, *args, **kwargs):
        raise NotImplementedError("'receive' method must be overriden.")


class ThreadedActor(Actor):

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
        logging.debug("Future: %s", __name__ + "::" + self.__class__.__name__)
        queue.put(self.receive(*args, **kwargs))
        return queue
