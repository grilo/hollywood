#!/usr/bin/env python

import logging
import time

logging.basicConfig(format='%(asctime)s::%(levelname)s::%(module)s::%(message)s')
logging.getLogger().setLevel('INFO')


import hollywood
import hollywood.http

actor = hollywood.System.new(hollywood.http.Server)
actor.tell()

while True:
    time.sleep(1)
    print "sleeping..."

hollywood.System.halt()
