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

import hollywood.future
import hollywood.exceptions


class Address(object):
    """
        This class is just syntatic sugar.

        Instead of going like:
            hollywood.actor.System.spawn(hollywood.net.http.Handler')
            hollywood.actor.System.tell(hollywood.net.http.Handler, message)
            hollywood.actor.System.ask(hollywood.net.http.Handler, message)
            hollywood.actor.System.stop(hollywood.net.http.Handler)

        You can:
            addr = hollywood.actor.System.spawn(hollywood.net.http.Handler)
            addr.tell(message)
            addr.ask(message)
			addr.stop()

        Underneath, the Address will call the actor system the same
        old way, providing referential transparency.
    """

    def __init__(self, actor):
        name = '/'.join([actor.__module__, actor.__class__.__name__])
        self.name = name.replace('.', '/')
        self.actor = actor

    def ask(self, *args, **kwargs):
        return self.actor.ask(*args, **kwargs)

    def tell(self, *args, **kwargs):
        return self.actor.tell(*args, **kwargs)

    def stop(self):
        return self.actor.stop()

    def __repr__(self):
        return self.name


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
        self.address = Address(self)
        self.inbox = Queue.Queue()
        self.is_alive = True

    def stop(self):
        logging.debug("[%s] Received stop signal.", self.address)
        self.is_alive = False

    def _loop(self):
        while self.is_alive:
            if self.inbox.empty():
                time.sleep(0.01)
                continue
            logging.debug("[%s] Inbox size: %i", self.address, self.inbox.qsize())
            args, kwargs = self.inbox.get_nowait()
            try:
                self.receive(*args, **kwargs)
            except Exception as error:
                logging.error(error, exc_info=True)
                raise hollywood.exceptions.ActorRuntimeError
        logging.debug("[%s] Shutting down.", self.address)

    def _loop(self):
        while self.is_alive:
            if self.inbox.empty():
                continue
            logging.debug("[%s] Inbox size: %i", self.address.name, self.inbox.qsize())
            future = self.inbox.get()
            args, kwargs = future.args, future.kwargs
            logging.debug("[%s] Processing: %s %s", self.address.name, args, kwargs)
            result = self._handle(*args, **kwargs)
            future.put(result)
        logging.info("[%s] Shutting down.", self.address.name)

    def _handle(self, *args, **kwargs):
        try:
            return self.receive(*args, **kwargs)
        except Exception as error:
            logging.error(error, exc_info=True)
            self.stop()
            raise hollywood.exceptions.ActorRuntimeError

    def tell(self, *args, **kwargs):
        return self.ask(*args, **kwargs)

    def ask(self, *args, **kwargs):
        logging.debug("[%s] Queueing message: %s %s", self.address.name, *args, **kwargs)
        future = hollywood.future.Base(*args, **kwargs)
        self.inbox.put(future)
        return future

    def receive(self, *args, **kwargs):
        raise NotImplementedError("'receive' method must be overriden.")


class Threaded(Base):
    """
    self.is_alive = True
        Spawn the event loop in a new thread.

        If 'ask'ed, computes the result in a separate thread
        and returns a future.
    """
    def __init__(self):
        super(Threaded, self).__init__()
        threading.Thread(name=self.address, target=self._loop).start()
