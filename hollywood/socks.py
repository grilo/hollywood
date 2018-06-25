#!/usr/bin/env python

import time
import logging
import socket

import hollywood.actor


class Server(hollywood.actor.Threaded):

    def receive(self, address, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Disable nagle algorithm, makes us look better in benchmarks
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind((address, port))
        sock.listen(10)
        return sock


class Listener(hollywood.actor.Threaded):

    def receive(self, server_socket):
        try:
            server_socket.settimeout(0)
            conn, addr = server_socket.accept()
            logging.debug("Received connection: %s %s", conn, addr)
            return conn, addr
        except socket.error: # Timeout
            return None, None
