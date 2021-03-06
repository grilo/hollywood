#!/usr/bin/env python

import logging
import datetime
import email
import ssl

import hollywood.actor
import hollywood.net.socks


class BadRequestError(Exception):
    """Unable to properly parse the request."""
    pass


class Request(object):

    """
        Attributes:
            method: GET, POST
            path: /, /metrics
            protocol: HTTP/1.0
            headers: {
                host: localhost:5000
                connection: keep-alive
            }
    """

    def __init__(self, socket, address, raw_string):

        self.socket = socket
        self.address = address
        raw_string = raw_string.strip()
        if not raw_string:
            logging.error("Empty request from: %s", address)
            raise BadRequestError

        try:
            lines = raw_string.strip().splitlines()
            logging.info("REQUEST: %s", lines[0])

            first_line = lines[0].split(' ')
            self.method = first_line[0]
            self.path = first_line[1]
            if len(first_line) == 3:
                self.protocol = first_line[2]

            self.headers = email.message_from_string('\r\n'.join(lines[1:]))
        except Exception:
            logging.error("Unable to parse request: [%s]", raw_string, exc_info=True)
            raise BadRequestError

    def send(self, response):
        self.socket.sendall(response.to_string())
        self.socket.close()


class Response(object):

    codes = {
        100: 'Continue',
        101: 'Switching Protocols',
        200: 'OK',
        201: 'Created',
        202: 'Accepted',
        203: 'Non-Authoritative Information',
        204: 'No Content',
        205: 'Reset Content',
        206: 'Partial Content',
        300: 'Multiple Choices',
        301: 'Moved Permanently',
        302: 'Found',
        303: 'See Other',
        304: 'Not Modified',
        305: 'Use Proxy',
        307: 'Temporary Redirect',
        400: 'Bad Request',
        401: 'Unauthorized',
        402: 'Payment Required',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        407: 'Proxy Authentication Required',
        408: 'Request Timeout',
        409: 'Conflict',
        410: 'Gone',
        411: 'Length Required',
        412: 'Precondition Failed',
        413: 'Request Entity Too Large',
        414: 'Request-URI Too Long',
        415: 'Unsupported Media Type',
        416: 'Requested Range Not Satisfiable',
        417: 'Expectation Failed',
        500: 'Internal Server Error',
        501: 'Not Implemented',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
        505: 'HTTP Version Not Supported',
    }

    def __init__(self, code=200):
        self.content = ''
        self.code = code
        self.protocol = 'HTTP/1.0'
        self.server = "Promenade/0.1 (noarch)"
        self.last_modified = ''
        self.content_type = 'text/html'
        self._redirect = None
        self._last_modified = None

    @property
    def date(self):
        """Return a string representation of a date according to RFC 1123
        (HTTP/1.0).

        The supplied date must be in UTC.

        """
        now = datetime.datetime.now()
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                 "Oct", "Nov", "Dec"][now.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, now.day, month,
                                                        now.year, now.hour,
                                                        now.minute, now.second)

    @property
    def content_length(self):
        return str(len(self.content))

    @property
    def last_modified(self):
        if not self._last_modified:
            self._last_modified = self.date
        return self._last_modified

    @property
    def redirect(self):
        return self._redirect

    @redirect.setter
    def redirect(self, new_url):
        self.code = 301
        self._redirect = new_url

    @last_modified.setter
    def last_modified(self, value):
        self._last_modified = value

    def to_string(self):
        header = ' '.join([self.protocol, str(self.code), Response.codes[self.code]])
        logging.debug("RESPONSE: %s", header)
        out = [
            header,
            'Date: ' + self.date,
            'Server: ' + self.server,
            'Last-Modified: ' + self.last_modified,
            'Content-Length: ' + self.content_length,
            'Content-Type: ' + self.content_type,
            'Connection: close',
            '\r\n',
            self.content,
        ]

        return '\n'.join(out)


class RequestHandler(hollywood.actor.Threaded):

    def receive(self, connection, address):
        data = connection.recv(8192) # Should be enough for everybody

        try:
            request = Request(connection, address, data)
            return request
        except BadRequestError:
            response = Response(400)
            connection.sendall(response.to_string())
            connection.close()


class ResponseHandler(hollywood.actor.Threaded):

    def receive(self, request):
        response = Response()
        response.content_type = 'text/html'
        response.content = "<html><h1>Well done!</h1></html>"
        request.send(response)
        return response


class Server(hollywood.actor.Threaded):
    """Usage:

    import hollywood
    import hollywood.net.http # Need to import all direct dependencies
    hollywood.System.spawn(hollywood.net.http.Server)
    hollywood.System.tell(port=5000)

    while True:
        logging.info("Actors alive!")
        time.sleep(2)

    The loop isn't actually necessary, keeps the main thread busy.
    """

    def __init__(self, response_handler=None):
        super(Server, self).__init__()
        if response_handler is None:
            response_handler = hollywood.System.spawn(response_handler)
        self.response_handler = response_handler

    def receive(self,
                address='0.0.0.0',
                port=5000,
                certfile=None):

        sock_server = hollywood.System.spawn(hollywood.net.socks.Server)
        sock_listener = hollywood.System.spawn(hollywood.net.socks.Listener)
        request_handler = hollywood.System.spawn(hollywood.net.http.RequestHandler)

        sock = sock_server.ask(address, port).get()
        if certfile:
            sock = ssl.wrap_socket(sock, certfile=certfile, server_side=True)
        sock_server.stop()

        logging.warning("Starting HTTP server in port: %i (%s)", port, address)

        while self.is_alive:
            conn, addr = sock_listener.ask(sock).get()
            if not conn:
                continue

            request = request_handler.ask(conn, addr).get()
            if request:
                self.response_handler.tell(request)
        logging.warning("HTTP Server actor shutting down.")
