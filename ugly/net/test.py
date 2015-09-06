import unittest

import multiprocessing
import threading
import socket
import contextlib
import time
import errno

from ugly.net import Server, wait_server_up, get_socket
from ugly.process import ProcessContext

class TestServer(unittest.TestCase):

    def test_server(self):
        """
        ``ugly.net.Server`` is a ` ``SocketServer.TCPServer`` `__ subclass.
        
        __ https://docs.python.org/2/library/socketserver.html
        """
        def serve():
            server = Server(
                address='localhost', port=9000, message='Server is up'
            )
            server.handle_request()
            server.server_close()

        with ProcessContext(target=serve):
            time.sleep(0.003)
            with contextlib.closing(get_socket()) as s:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

                self.assertEquals('Server is up', msg)


    def test_with(self):
        """
        ``ugly.net.Server`` is also a context manager. If given to an ``with``
        statement, the server will start at the beginning and stop at the end
        of the block.
        """
        with Server(message='Server is up') as server:
            with contextlib.closing(get_socket()) as s:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

                self.assertEquals('Server is up', msg)

        with contextlib.closing(get_socket(timeout=0.00001)) as s:
            with self.assertRaises(socket.error) as a:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

class TestWaiters(unittest.TestCase):

    def test_wait_server_up(self):
        """
        ``wait_server_up()`` will block until there is a socket listening at
        the given port from the given address.
        """
        delay = 0.01
        start = time.time()

        def serve(condition):
            time.sleep(delay)

            server = Server(message='Server is up')

            thread = threading.Thread(target=server.serve_forever)
            thread.start()

            condition.acquire()
            condition.wait()

            server.shutdown()
            thread.join()

        condition = multiprocessing.Condition()
        with ProcessContext(target=serve, args=(condition,)) as pc:
            wait_server_up('localhost', 9000, timeout=0.0001)

            self.assertTrue(time.time() - start > delay)

            condition.acquire()
            condition.notify_all()
            condition.release()

    def test_wait_server_up_does_not_acquire_port(self):
        """
        ``wait_server_up()`` cannot impede other processes of capturing the
        port.
        """
        delay = 0.01

        def serve(condition):
            time.sleep(delay)

            server = Server(message='Server is up')

            thread = threading.Thread(target=server.serve_forever)
            thread.start()

            condition.acquire()
            condition.wait()

            server.shutdown()
            thread.join()

        condition = multiprocessing.Condition()
        with ProcessContext(target=serve, args=(condition,)) as pc:
            wait_server_up('localhost', 9000, timeout=delay*2)

            with contextlib.closing(get_socket()) as s:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

                self.assertEquals('Server is up', msg)

            condition.acquire()
            condition.notify_all()
            condition.release()

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.net.net').load_tests

if __name__ == "__main__":
    unittest.main()
