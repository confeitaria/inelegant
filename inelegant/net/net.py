#
# Copyright 2015, 2016 Adam Victor Brandizzi
#
# This file is part of Inelegant.
#
# Inelegant is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Inelegant is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Inelegant.  If not, see <http://www.gnu.org/licenses/>.

import socket
import errno
import time
import contextlib
import SocketServer
import threading


def wait_server_up(host, port, timeout=1, tries=100):
    """
    This function blocks the execution until connecting successfully to the
    given address and port.

    It is useful because server functions, classes, processes etc. frequently
    take some time to start listening a port - they have to load resources,
    process them etc. A common workaround is to use ``time.sleep()`` or similar
    function to block the execution for a small amount of time. However, this
    is both unreliable and wasteful. It is unreliable because the server may
    occasionally take more time to boot than the function sleeps. It is also
    wasteful since, to avoid the unreliability, we tend to wait for a larger
    time than the server requires in most situations.

    With ``wait_server_up()`` we can avoid it. It will block only until the
    port is serving. For example, if we have a "slow server" as the one
    below...

    ::

    >>> import inelegant.net, multiprocessing, socket, contextlib, time
    >>> def serve():
    ...     time.sleep(0.05)
    ...     server = inelegant.net.Server(
    ...         'localhost', 9000, message='my message'
    ...     )
    ...     server.serve_forever()

    ...that we start in a different process...

    ::

    >>> process = multiprocessing.Process(target=serve)

    ...trying to get the value just after starting the process will probably
    fail::

    >>> process.start()
    >>> with contextlib.closing(socket.socket()) as s:
    ...     s.connect(('localhost', 9000))
    ...     s.recv(10)
    Traceback (most recent call last):
     ...
    error: [Errno 111] Connection refused
    >>> process.terminate()

    Now, if we use ``wait_server_up()``, the port will be surely available::

    >>> process = multiprocessing.Process(target=serve)
    >>> process.start()
    >>> with contextlib.closing(socket.socket()) as s:
    ...     wait_server_up('localhost', 9000)
    ...     s.connect(('localhost', 9000))
    ...     s.recv(10)
    'my message'
    >>> process.terminate()

    And the best thing is, it will take only a minimum amount of time::

    >>> process = multiprocessing.Process(target=serve)
    >>> process.start()
    >>> start = time.time()
    >>> wait_server_up('localhost', 9000)
    >>> 0.05 < time.time() - start < 0.1
    True
    >>> process.terminate()
    >>> process.join()

    The function will wait until a timeout is reached. By default, the timeout
    is one second. However, it can be changed to wait more (or less) type with
    the ``timeout`` argument. It expects a value in seconds.

    ::

    >>> start = time.time()
    >>> wait_server_up('localhost', 9000, timeout=0.05)
    Traceback (most recent call last):
     ...
    Exception: Connection to server failed after 100 attempts
    >>> 0.05 < time.time() - start < 0.1
    True

    If a network error happens, it will raise the exception, except if the
    connection is refused. If an conection is refused, this error will be
    ignored since it probably means the server is not up yet. However, this
    error will only be ignored for <tries> times (by default 1000). Once the
    connection is refuses for more than <tries> times, an exception will be
    raised.
    """
    socket_timeout = float(timeout) / tries
    if socket_timeout < 0.0001:
        socket_timeout = 0.0001

    for i in xrange(tries):
        s = socket.socket()
        s.settimeout(socket_timeout)
        with contextlib.closing(s):
            try:
                s.connect((host, port))
                break
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    time.sleep(socket_timeout)
                else:
                    raise
    else:
        raise Exception(
            'Connection to server failed after {0} attempts'.format(tries)
        )


def wait_server_down(host, port, timeout=1, tries=100):
    """
    This function blocks until the given port is free at the given address.

    It is useful because server functions, classes, processes etc. frequently
    take some time to stop listening a port - they have to unload resources,
    close files etc. A common workaround is to use ``time.sleep()`` or similar
    function to block the execution for a small amount of time. However, this
    is both unreliable and wasteful. It is unreliable because the server may
    occasionally take more time to shut down than the function sleeps. It is
    also wasteful since, to avoid the unreliability, we tend to wait for a
    larger times than the server requires in most situations to shut down.

    With ``wait_server_down()`` we can avoid it. It will block only until
    nobody is listening the port anymore. For example, if we have a "slow
    server" as the one below...

    ::

    >>> import inelegant.net, threading, contextlib, socket
    >>> server = inelegant.net.Server('localhost', 9000, message='my message')
    >>> def serve():
    ...     server.serve_forever() # This only stops the loop
    ...     time.sleep(0.001)
    ...     server.server_close()  # This effectively close the connection

    ...that we start in a different thread...

    ::

    >>> thread = threading.Thread(target=serve)

    ...we could not bind to the same port while it is not finished.::

    >>> thread.start()
    >>> with contextlib.closing(socket.socket()) as s:
    ...     wait_server_up('localhost', 9000)
    ...     server.shutdown()
    ...     s.bind(('localhost', 9000))
    Traceback (most recent call last):
     ...
    error: [Errno 98] Address already in use
    >>> thread.join()

    Now, if we use ``wait_server_down()``, the port will be surely available::

    >>> server = inelegant.net.Server('localhost', 9000, message='my message')
    >>> thread = threading.Thread(target=serve)
    >>> thread.start()
    >>> with contextlib.closing(socket.socket()) as s:
    ...     wait_server_up('localhost', 9000)
    ...     server.shutdown()
    ...     wait_server_down('localhost', 9000)
    ...     s.bind(('localhost', 9000))
    >>> thread.join()

    And the best thing is, it will take only a minimum amount of time::

    If an conection is refused or reset, this error will be ignored since it
    probably means respectively the server is not up (as excepted) or just went
    down during the connection, which is acceptable.

    The function will wait until a timeout is reached. By default, the timeout
    is one second. However, it can be changed to wait more (or less) type with
    the ``timeout`` argument. It expects a value in seconds.

    ::

    >>> with Server():
    ...     start = time.time()
    ...     wait_server_down('localhost', 9000, timeout=0.05)
    Traceback (most recent call last):
     ...
    Exception: Server stayed up after 100 connection attempts. May it be runni\
ng from a process outside the tests?
    >>> 0.05 < time.time() - start < 0.1
    True
    """
    socket_timeout = float(timeout) / tries
    if socket_timeout < 0.0001:
        socket_timeout = 0.0001

    for i in xrange(tries):
        s = socket.socket()
        with contextlib.closing(s):
            try:
                s.settimeout(socket_timeout)
                s.connect((host, port))
                time.sleep(socket_timeout)
            except socket.timeout:
                continue
            except socket.error as e:
                if e.errno in (errno.ECONNREFUSED, errno.ECONNRESET):
                    break
                elif e.errno == errno.ETIMEDOUT:
                    continue
                else:
                    raise
    else:
        raise Exception(
            'Server stayed up after {0} connection attempts. '
            'May it be running from a process outside the tests?'.format(tries)
        )


class Server(SocketServer.TCPServer):
    """
    ``inelegant.net.Server`` is a very simple TCP server that only responds
    with the same message, given to its constructor::

    >>> server = Server(
    ...     host='localhost', port=9000, message='My message'
    ... )

    It is a ``SocketServer.TCPServer`` subclass, so one can use it as one would
    use any TCP server. For example, we can write a function that waits for a
    request, responds it and shut down the server::

    >>> def serve():
    ...     server.handle_request()
    ...     server.server_close()

    If we give it to a process...

    ::

    >>> import multiprocessing, time
    >>> process = multiprocessing.Process(target=serve)
    >>> process.daemon = True
    >>> process.start()
    >>> time.sleep(0.01)

    ...we can get the answer::

    >>> with contextlib.closing(socket.socket()) as s:
    ...     s.connect(('localhost', 9000))
    ...     s.recv(10)
    'My message'
    >>> process.join()

    You may prefer, however, to use it with an ``with`` statement. In this
    case, the server is started up and shut down automatically::

    >>> with Server(message='My message'):
    ...     with contextlib.closing(socket.socket()) as s:
    ...         s.connect(('localhost', 9000))
    ...         s.recv(10)
    'My message'
    >>> with contextlib.closing(socket.socket()) as s:
    ...     s.connect(('localhost', 9000))
    ...     s.recv(10)
    Traceback (most recent call last):
     ...
    error: [Errno 111] Connection refused
    """

    def __init__(
            self, host='localhost', port=9000, message='Message sent',
            wait_for_release=0.001):
        self.host = host
        self.port = port
        self.message = message
        self.wait_for_release = wait_for_release

        self.init_lock = threading.Lock()

    def handle_request(self):
        self._lazy_init()

        return SocketServer.TCPServer.handle_request(self)

    def serve_forever(self, poll_interval=0.001):
        self._lazy_init()

        SocketServer.TCPServer.serve_forever(self, poll_interval)

    def server_close(self):
        if self._is_initialized():
            SocketServer.TCPServer.server_close(self)

    def shutdown(self):
        if self._is_initialized():
            SocketServer.TCPServer.shutdown(self)

    def __enter__(self):
        self.thread = threading.Thread(target=self.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        self.init_lock.acquire()
        self.init_lock.release()
        time.sleep(self.wait_for_release)

        return self

    def __exit__(self, type, value, traceback):
        with self.init_lock:
            if self._is_initialized():
                self.shutdown()
                self.server_close()
                self.thread.join()

    def _lazy_init(self):
        with self.init_lock:
            if not self._is_initialized():
                SocketServer.TCPServer.__init__(
                    self, (self.host, self.port), ServerHandler)

    def _is_initialized(self):
        return hasattr(self, 'socket')


class ServerHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        self.request.sendall(self.server.message+'\0')


def get_socket(timeout=None):
    """
    This function creates sockets. Its main appeal is that one can give the
    timeout as an argument::

    >>> import socket
    >>> s = get_socket(timeout=3.0)
    >>> isinstance(s, socket.socket)
    True
    >>> s.gettimeout()
    3.0
    """
    s = socket.socket()
    s.settimeout(timeout)

    return s
