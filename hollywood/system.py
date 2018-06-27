#!/usr/bin/env python

import time
import threading
import logging

# Clean shutdown with ctrl-c
import sys
import signal

import hollywood.actor
import hollywood.exceptions

def signal_handler(sig, frame):
    System.halt()
    sys.exit(1)
signal.signal(signal.SIGINT, signal_handler)


class System(object):

    address_actor = {}
    processes = {}
    actor_lock = threading.RLock()

    @classmethod
    def init(cls):
        logging.warning("Initializing actor system.")
        work = [hollywood.actor.Base]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                cls.register(child)
                work.append(child)

    @classmethod
    def register(cls, actor):
        address_list = [actor.__module__ + '/' + actor.__name__]
        if hasattr(actor, 'address'):
            address_list += actor.address

        for addr in address_list:
            normalized_addr = addr.replace('.', '/')
            logging.info("Registering: %s", normalized_addr)
            cls.address_actor[normalized_addr] = actor

    @classmethod
    def new(cls, address):
        with cls.actor_lock:
            if address not in cls.processes:
                cls.processes[address] = {}
            logging.debug("Spawning new actor: %s", address)
            actor = cls.address_actor[address]()
            cls.processes[address][actor.uuid] = actor
            actor.start()
        return ActorRef(address)

    @classmethod
    def ask(cls, actor_address, *args, **kwargs):
        if not actor_address in cls.address_actor:
            raise hollywood.exceptions.ActorNotRegisteredError(actor_address)

        if not actor_address in cls.processes:
            cls.new(actor_address)

        # This is very basic: get the first actor able to handle
        # this request and ask him to return a promise. Ideally
        # we would have a Router actor handling these requests
        # and posting them to the correct inbox with a little
        # more consideration. Example:
        # - Round robin scheduling
        # - Spawning new actors if the current ones are taking too long
        for actor in cls.processes[actor_address].values():
            try:
                return actor.ask(*args, **kwargs)
            except hollywood.exceptions.ActorRuntimeError:
                # TODO Notify a supervisor to restart the actor and
                # resend the message.
                return None

    @classmethod
    def tell(cls, actor_address, *args, **kwargs):
        cls.ask(actor_address, *args, **kwargs)

    @classmethod
    def stop(cls, address):
        if address not in cls.processes.keys():
            logging.warning("Unable to halt unknown address: %s", address)
            return
        with cls.actor_lock:
            logging.info("Halting: %s (%i actors)", address, len(cls.processes[address]))
            for actor in cls.processes[address].values():
                actor.stop()
            for uuid in cls.processes[address].keys():
                del cls.processes[address][uuid]

    @classmethod
    def halt(cls):
        logging.warning("Halting all actors.")
        with cls.actor_lock:
            for address in cls.processes:
                cls.stop(address)

        while threading.active_count() > 1:
            for thread in threading.enumerate():
                logging.warning("Waiting for thread to exit: %s", thread.name)
            time.sleep(1)
        logging.warning("Halting completed.")


    @classmethod
    def status(cls):
        with cls.actor_lock:
            addresses = 0
            processes = 0
            for actors in cls.processes.values():
                addresses += 1
                processes += len(actors)
        return {
            'addresses': addresses,
            'processes': processes,
        }


class ActorRef(object):
    """
        This class is just syntatic sugar.

        Instead of going like:
            hollywood.actor.System.new('http/Handler')
            hollywood.actor.System.tell('http/Handler', message)
            hollywood.actor.System.ask('http/Handler', message)
            hollywood.actor.System.stop('http/Handler')

        You can:
            ref = hollywood.actor.System.new('http/Handler')
            ref.tell(message)
            ref.ask(message)
            ref.stop()

        Underneath, the ActorRef will call the actor system the same
        old way, providing referential transparency.
    """
    def __init__(self, address):
        self.address = address

    def tell(self, *args, **kwargs):
        return System.tell(self.address, *args, **kwargs)

    def ask(self, *args, **kwargs):
        return System.ask(self.address, *args, **kwargs)

    def stop(self):
        return System.stop(self.address)
