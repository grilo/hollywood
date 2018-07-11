#!/usr/bin/env python

import logging
import time

logging.basicConfig(format='%(asctime)s::%(levelname)s::%(module)s::%(message)s')
logging.getLogger().setLevel('INFO')


import hollywood
import hollywood.fun
import hollywood.actor
import hollywood.net.http


class R(hollywood.actor.Threaded):

    @hollywood.fun.patternmatch(hollywood.net.http.Request)
    def receive(self, request):
        response = hollywood.net.http.Response()
        response.content_type = 'text/html'
        response.content = "<html><h1>Well done!</h1></html>"
        request.send(response)
        return response

actor = hollywood.System.spawn(hollywood.net.http.Server, hollywood.System.spawn(R))
actor.tell()

print "SIGKILL (ctrl-C) stops."
while True:
    time.sleep(1)

hollywood.System.halt()
