#!/usr/bin/env python

import time
import logging
import socket
import sys

import actor

class SocketServer(actor.ThreadedActor):

    def receive(self, address='0.0.0.0', port=1025):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Disable nagle algorithm, makes us look better in benchmarks
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind((address, port))
        sock.listen(1)
        sock.setblocking(False)

        SocketHandler().tell(sock)


class SocketHandler(actor.ThreadedActor):

    def receive(self, server_socket):
        try:
            conn, addr = server_socket.accept()
            logging.debug("Received connection: %s %s", conn, addr)
            # Spawn a handler whenever a connection is received
            HTTPHandler().tell(conn, addr, self)
        except socket.error:
            pass
        # Put the listener back in the queue
        self.tell(server_socket)


class HTTPHandler(actor.ThreadedActor):

    def receive(self, connection, address, server):
        data = connection.recv(8192) # Should be enough for everybody
        logging.debug("Received data!: %s", data)

        connection.sendall("""HTTP/1.1 200 OK
Date: Sun, 18 Oct 2009 08:56:53 GMT
Server: Apache/2.2.14 (Win32)
Last-Modified: Sat, 20 Nov 2004 07:16:26 GMT
Content-Length: 44
Connection: close
Content-Type: text/html

<html><body><h1>It works!</h1></body></html>""")
        connection.close()
        self.stop()


logging.basicConfig(format='%(asctime)s::%(levelname)s::%(module)s::%(message)s')
logging.getLogger().setLevel(getattr(logging, 'INFO'))

x = SocketServer()
x.tell(port=5000)

while True:
    time.sleep(0.2)
    print 'Actors alive:', len(actor.Registry.actors.keys())

print "Done!"
