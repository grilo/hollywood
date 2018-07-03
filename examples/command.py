#!/usr/bin/env python

import hollywood
import hollywood.shell

actor = hollywood.System.new(hollywood.shell.Command)
future = actor.ask('ls -la')
rc, out, err = future.get(timeout=1)
print "Output is", out

hollywood.System.halt()
