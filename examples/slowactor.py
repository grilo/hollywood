#!/usr/bin/env python

import logging
import time

logging.basicConfig(format='%(asctime)s::%(levelname)s::%(module)s::%(message)s')
#logging.getLogger().setLevel('INFO')
logging.getLogger().setLevel('WARNING')


import hollywood
import hollywood.fun
import hollywood.actor
import hollywood.net.http


class SlowActor(hollywood.actor.Threaded):

    @hollywood.fun.patternmatch(str)
    def receive(self, message):
        import time
        time.sleep(1)
        print message, "Yes, I'm done! Still have %i message in the inbox." % (self.inbox.qsize())

actor = hollywood.System.spawn(SlowActor)
print "Telling 5 times."
for i in range(5):
    actor.tell("Are you done with (%i)?" % (i))

i = 7
while i:
    time.sleep(1)
    i -= 1

hollywood.System.halt()
