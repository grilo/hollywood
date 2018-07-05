#!/usr/bin/env python

import logging
import shlex
import subprocess

import hollywood.actor


class Command(hollywood.actor.Threaded):

    def receive(self, command, env=None, shell=False):
        if env is None:
            env = {}
        logging.debug("Running command: %s", command)
        cmd = shlex.split(command.encode('utf-8'))
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env,
                                shell=shell)
        out, err = proc.communicate()
        return_code = proc.returncode
        return return_code, out, err
