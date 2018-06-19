#!/usr/bin/env python

import threading
import logging

import hollywood.actor

# Clean shutdown with ctrl-c
import sys
import signal
def signal_handler(signal, frame):
        System.halt()
        sys.exit(1)
signal.signal(signal.SIGINT, signal_handler)


class System(object):

    address_actor = {}
    processes = {}
    actor_lock = threading.RLock()

    @classmethod
    def init(cls):
        subclasses = set()
        work = [hollywood.actor.Base]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                cls.register(child)
                work.append(child)

    @classmethod
    def register(cls, actor):
        for addr in actor.address:
            normalized_addr = addr.replace('.', '/')
            logging.info("Registering: %s", normalized_addr)
            cls.address_actor[normalized_addr] = actor

    @classmethod
    def tell(cls, address, *args, **kwargs):
        cls.ask(address, *args, **kwargs)

    @classmethod
    def ask(cls, address, *args, **kwargs):
        if not cls.processes[address]:
            cls.new(address)
        # This is very basic: get the first actor able to handle
        # this request and ask him to return a promise. Ideally
        # we would have a Router actor handling these requests
        # and posting them to the correct inbox with a little
        # more consideration. Example:
        # - Round robin scheduling
        # - Spawning new actors if the current ones are taking too long
        for uuid, actor in cls.processes[address].items():
            return actor.ask(*args, **kwargs)

    @classmethod
    def new(cls, address):
        with cls.actor_lock:
            if address not in cls.processes:
                cls.processes[address] = {}
            actor = cls.address_actor[address]()
            cls.processes[address][actor.uuid] = actor
            actor.start()
        return ActorRef(address)

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
        with cls.actor_lock:
            logging.warning("Halting all actors.")
            for address in cls.processes.keys():
                cls.stop(address)
            logging.info("Halting completed.")
            logging.info("If process doesn't exit, threads are still blocked (kill?).")

    @classmethod
    def status(cls):
        with cls.actor_lock:
            addresses = 0
            processes = 0
            for addr in cls.processes.keys():
                addresses += 1
                for actor in cls.processes[addr]:
                    processes += 1
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
