#!/usr/bin/env python

import time
import logging
import socket

import actor


class Server(actor.ThreadedActor):

    def receive(self, address, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Disable nagle algorithm, makes us look better in benchmarks
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind((address, port))
        sock.listen(5)
        return sock


class Listener(actor.ThreadedActor):

    def receive(self, server_socket):
        try:
            server_socket.settimeout(2)
            conn, addr = server_socket.accept()
            logging.debug("Received connection: %s %s", conn, addr)
            return conn, addr
        except socket.error: # Timeout
            pass
        return None, None