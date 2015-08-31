import unittest

import multiprocessing
import socket
import contextlib
import time
import errno

from ugly.net import Server, wait_server_up, get_socket

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

        process = multiprocessing.Process(target=serve)
        process.daemon = True
        process.start()
        time.sleep(0.003)

        with contextlib.closing(get_socket()) as s:
            s.connect(('localhost', 9000))
            msg = s.recv(len('Server is up'))

            self.assertEquals('Server is up', msg)

        process.join()


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

    def test_start_delay(self):
        """
        Sometimes we want our server to delay its effective port listening. We
        can define the amount of seconds to be delayed with the ``start_delay``
        argument.
        """
        with Server(message='Server is up', start_delay=0.01) as server:
            with contextlib.closing(get_socket(timeout=0.0001)) as s:
                with self.assertRaises(socket.error) as a:
                    s.connect(('localhost', 9000))
                    msg = s.recv(len('Server is up'))

            time.sleep(0.02)

            with contextlib.closing(get_socket()) as s:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

                self.assertEquals('Server is up', msg)

    def test_with_shutdown_before_startup(self):
        """
        If a server is requested to shutdown even before starting up,
        ``ugly.net.Server`` should handle it appropriately.
        """
        with Server(start_delay=0.1) as server:
            pass

    def test_start_delay_no_block(self):
        """
        If we give a positive ``start_delay`` to the server, it should **not**
        block the parent thread.
        """
        delay = 0.1
        start = time.time()
        with Server(start_delay=delay) as server:
            self.assertTrue(time.time() - start < delay)

class TestWaiters(unittest.TestCase):

    def test_wait_port_up(self):
        """
        ``wait_server_up()`` will block until there is a socket listening at
        the given port from the given address.
        """
        delay = 0.01
        start = time.time()
        with Server(start_delay=delay) as server:
            wait_server_up('localhost', 9000, timeout=0.001)

            self.assertTrue(time.time() - start > delay)

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.net.net').load_tests

if __name__ == "__main__":
    unittest.main()
