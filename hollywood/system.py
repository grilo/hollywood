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

    processes = {}
    actor_lock = threading.RLock()

    @classmethod
    def new(cls, actor_class):
        actor = actor_class()
        cls.processes[actor.address.name] = actor
        return actor.address

    @classmethod
    def halt(cls):
        logging.warning("Shutdown sequence initiated.")
        with cls.actor_lock:

            address_list = cls.processes.keys()
            for address in address_list:
                logging.info("Halting: %s", address)
                cls.processes[address].stop()
                del cls.processes[address]

        while threading.active_count() > 1:
            for thread in threading.enumerate():
                logging.warning("Waiting for thread to exit: %s", thread.name)
            time.sleep(1)
        logging.warning("Shutdown complete.")


    @classmethod
    def alive(cls):
        return len(cls.processes)
