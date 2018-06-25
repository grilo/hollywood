#!/usr/bin/env python

"""
    Actor base class and backends.

    An actor:
        - Is an independent unit of computation.
        - May have one or more addresses.
        - Has an inbox (the code below implements this with a Queue).
        - Processes messages from the inbox sequentially.
        - May create other actors.
        - May communicate with other actors via their address.

    An actor is no actor. Actors are useful when they come in systems.
    Systems are a set of actors which provide some actual functionality
    and enable all the actors to work with eachother.

    In pure implementions, the inbox of an actor would be an actor in
    itself.
"""

import time
import Queue
import threading
import logging
import uuid


class Base(object):
    """Abstract-y class that implements a synchronous actor.

    A synchronous actor is completely unusable, do not subclass this directly.
    Instead, prefer one of the backends (Threaded).

    The start/stop method control whether the event loop is running or not.

    For every iteration of the event loop, one message is extracted from the
    inbox and passed as-is to the receive(*message) method.

    The method 'tell' is "fire-and-forget": will cause the actor to do some work
    but always returns None.

    The method 'ask' is very similar to tell, but returns a future with the
    result of the computation.
    """

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
            args, kwargs = self.inbox.get_nowait()
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
    """
        Spawn the event loop in a new thread.

        If 'ask'ed, computes the result in a separate thread
        and returns a future.
    """


    def start(self):
        name = __name__ + '/' + self.__class__.__name__
        threading.Thread(name=name.replace('.', '/'),
                         target=self._loop).start()

    def ask(self, *args, **kwargs):
        """Return a future with the result.

        This is specific implementation skips the actor's inbox and directly
        runs the computation in a separate thread.

        In regular circumstances, the 'ask' would be put in the inbox and
        processed with no higher priority, but I didn't find an elegant way
        to implement that.
        """
        queue = Queue.Queue()
        name = __name__ + '/' + self.__class__.__name__
        threading.Thread(name=name.replace('.', '/') + '/Future',
                         target=self.__future,
                         args=(queue, args),
                         kwargs=kwargs).start()
        return queue

    def __future(self, queue, args, **kwargs):
        """
            Wraps the 'receive' method by capturing its output and returning
            it in the form of a Queue.Queue.

            You can then do 'obj.get()' to obtain the result (blocks if
            not done, check the Queue.Queue for other non-blocking options).
        """
        logging.debug("Future::%s", __name__ + "::" + self.__class__.__name__)
        queue.put(self.receive(*args, **kwargs))
