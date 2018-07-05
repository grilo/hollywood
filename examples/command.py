#!/usr/bin/env python

import hollywood
import hollywood.os.shell

actor = hollywood.System.new(hollywood.os.shell.Command)
future = actor.ask('ls -la')
rc, out, err = future.get(timeout=1)
print "Output is", out

hollywood.System.halt()
