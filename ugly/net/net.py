import socket
import errno
import time
import contextlib
import SocketServer
import threading

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
        self.thread = threading.Thread(target=self._start)
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

    def _start(self):
        self.serve_forever()

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
