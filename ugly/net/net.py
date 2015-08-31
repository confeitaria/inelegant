import socket
import errno
import time
import contextlib
import SocketServer
import threading

def wait_server_up(address, port, tries=1000, timeout=1):
    """
    This function blocks the execution until connecting successfully to the
    given address and port, or until an error happens - in this case, it will
    raise the exception.

    If an conection is refused, this error will be ignored since it probably
    means the server is not up yet. However, this error will only be ignored
    for <tries> times (by default 1000). Once the connection is refuses for more
    than <tries> times, an exception will be raised.
    """
    for i in xrange(tries):
        s = socket.socket()
        s.settimeout(timeout)
        with contextlib.closing(s):
            try:
                s.connect((address, port))
                break
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    time.sleep(timeout)
                else:
                    raise
    else:
        raise Exception(
            'Connection to server failed after {0} attempts'.format(tries)
        )

class Server(SocketServer.TCPServer):
    """
    ``ugly.net.Server`` is a very simple TCP server that only responds with the
    same message, given to its constructor::

    >>> server = Server(
    ...     address='localhost', port=9000, message='My message'
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

    You may prefer, however, to use it with an ``with`` statement. In this case,
    the server is started up and shut down automatically::

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

    You can make the class wait a bit before binding to the port::

    >>> start = time.time()
    >>> with Server(start_delay=0.1):
    ...     time.time() - start < 0.1
    ...     with contextlib.closing(socket.socket()) as s:
    ...         try:
    ...             s.connect(('localhost', 9000))
    ...             s.recv(10)
    ...         except socket.error as e:
    ...             print e
    True
    [Errno 111] Connection refused

    The ``start_delay`` argument is the *minimum* time the class will wait until
    grabbing the port, so it is well advisible to wait a bit more before
    connecting::

    >>> start = time.time()
    >>> with Server(message='My message', start_delay=0.1):
    ...     time.time() - start < 0.1
    ...     time.sleep(0.11)
    ...     time.time() - start < 0.1
    ...     with contextlib.closing(socket.socket()) as s:
    ...         s.connect(('localhost', 9000))
    ...         s.recv(10)
    True
    False
    'My message'

    Why would anyone want the server to be slower to go up? Mostly to test code
    that should wait for a port to be listening - basically, the
    ``wait_server_up`` function::

    >>> start = time.time()
    >>> with Server(message='My message', start_delay=0.1):
    ...     wait_server_up('localhost', 9000, timeout=0.001)
    ...     time.time() - start > 0.1
    True
    """

    def __init__(
            self, address='localhost', port=9000, message='Message sent',
            start_delay=0, wait_for_release=0.001
        ):
        self.address = address
        self.port = port
        self.message = message
        self.start_delay = start_delay
        self.wait_for_release = wait_for_release

        self.init_lock = threading.Lock()

    def handle_request(self):
        self._lazy_init()

        return SocketServer.TCPServer.handle_request(self)

    def serve_forever(self, poll_interval=0.001):
        self._lazy_init()

        SocketServer.TCPServer.serve_forever(self, poll_interval)

    def __enter__(self):
        self.thread = threading.Thread(target=self.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        if self.start_delay <= 0:
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
                time.sleep(self.start_delay)
                SocketServer.TCPServer.__init__(
                    self, (self.address, self.port), ServerHandler
                )

    def _is_initialized(self):
        return hasattr(self, 'socket')

class ServerHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        self.request.sendall(self.server.message+'\0')

def get_socket(timeout=0):
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

