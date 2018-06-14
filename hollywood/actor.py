#!/usr/bin/env python

import time
import Queue
import threading
import logging
import uuid

import signal
import sys


# Clean shutdown with ctrl-c
def signal_handler(signal, frame):
        Registry.halt()
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


class Registry(object):

    actors = {}
    actor_lock = threading.RLock()

    @classmethod
    def register(cls, actor):
        with cls.actor_lock:
            cls.actors[actor.uuid] = actor

    @classmethod
    def unregister(cls, uuid):
        with cls.actor_lock:
            logging.debug("Halting: %s", uuid)
            if uuid in cls.actors:
                del cls.actors[uuid]

    @classmethod
    def halt(cls, block=True, timeout=None):
        logging.debug("Halting all actors.")
        with cls.actor_lock:
            for uuid in reversed(cls.actors.keys()):
                cls.actors[uuid].stop()
                Registry.unregister(uuid)
            logging.debug("Halting completed.")


class Actor(object):

    def __init__(self):
        self.inbox = Queue.Queue()
        self.running = True
        self.uuid = str(uuid.uuid4()) + "::" + self.__class__.__name__
        Registry.register(self)
        self.start()

    def start(self):
        raise NotImplementedError("Do not instantiate Actor class directly, use the flavours.")

    def stop(self):
        logging.debug("[%s] Received stop signal.", self.uuid)
        self.running = False
        Registry.unregister(self.uuid)

    def _loop(self):

        while self.running:

            if self.inbox.empty():
                time.sleep(0.0001)
                continue

            try:
                args, kwargs = self.inbox.get(False)
                self.receive(*args, **kwargs)
                self.inbox.task_done()
            except:
                logging.critical("[%s] Something went wrong...", self.uuid, exc_info=True)
                Registry.halt()

        logging.debug("[%s] Shutting down.", self.uuid)

    def tell(self, *args, **kwargs):
        self.inbox.put((args, kwargs))
        return self

    def ask(self, *args, **kwargs):
        return self.receive(*args, **kwargs)

    def receive(self, *args, **kwargs):
        raise NotImplementedError("'receive' method must be overriden.")


class ThreadedActor(Actor):

    def start(self):
        thread = threading.Thread(target=self._loop)
        thread.start()

    def ask(self, *args, **kwargs):
        queue = Queue.Queue()
        thread = threading.Thread(target=self.future, args=(queue, args), kwargs=kwargs)
        thread.start()
        return queue

    def future(self, queue, args, **kwargs):
        """
            Wraps the 'receive' method by capturing its output and returning
            it in the form of a Queue.Queue.

            You can then do 'obj.get()' to obtain the result (blocks if
            not done, check the Queue.Queue for other non-blocking options).
        """
        logging.debug("Spawned: %s", self.__class__.__name__)
        queue.put(self.receive(*args, **kwargs))
        return queue

