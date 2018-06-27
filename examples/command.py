#!/usr/bin/env python

import hollywood
import hollywood.shell

hollywood.System.init()

future = hollywood.System.ask('hollywood/shell/Command', 'ls -la')
rc, out, err = future.get(timeout=1)
print "Output is", out

hollywood.System.halt()
