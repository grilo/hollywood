#!/usr/bin/env python

import time
import logging

import hollywood
import hollywood.shell

logging.basicConfig(format='%(asctime)s::%(levelname)s::%(module)s::%(message)s')
logging.getLogger().setLevel('DEBUG')

actor = hollywood.System.new(hollywood.shell.Command)

for i in range(3):
    actor.tell('sleep 3')

print "This should take 9 seconds."
print "Actor accepts items in queue without blocking."
print "Actor processes items synchronously."

time.sleep(10)

print "Should exit almost instantly."
hollywood.System.halt()
