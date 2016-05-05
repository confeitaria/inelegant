#!/usr/bin/env python
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

import unittest

import multiprocessing
import threading
import socket
import contextlib
import time
import errno

from inelegant.net import Server, wait_server_up, wait_server_down, get_socket
from inelegant.process import Process

from inelegant.finder import TestFinder


class TestServer(unittest.TestCase):

    def test_server(self):
        """
        ``inelegant.net.Server`` is a ` ``SocketServer.TCPServer`` `__
        subclass.

        __ https://docs.python.org/2/library/socketserver.html
        """

        def serve():
            server = Server(
                host='localhost', port=9000, message='Server is up')
            server.handle_request()
            server.server_close()

        with Process(target=serve):
            time.sleep(0.01)
            with contextlib.closing(get_socket()) as s:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

                self.assertEquals('Server is up', msg)

    def test_with(self):
        """
        ``inelegant.net.Server`` is also a context manager. If given to an
        ``with`` statement, the server will start at the beginning and stop at
        the end
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

        def serve():
            time.sleep(delay)

            server = Server(message='Server is up')

            thread = threading.Thread(target=server.serve_forever)
            thread.start()

            yield  # Should wait until the assert is done.
            server.shutdown()
            thread.join()

        with Process(target=serve) as pc:
            wait_server_up('localhost', 9000)
            self.assertTrue(time.time() - start > delay)

            pc.go()  # Once the assert is done, proceed.

    def test_wait_server_up_does_not_acquire_port(self):
        """
        ``wait_server_up()`` cannot impede other processes of capturing the
        port.
        """
        delay = 0.01

        def serve():
            time.sleep(delay)

            server = Server(message='Server is up')

            thread = threading.Thread(target=server.serve_forever)
            thread.start()

            yield  # Wait until asserts are checkd.
            server.shutdown()
            thread.join()

        with Process(target=serve) as pc:
            wait_server_up('localhost', 9000, timeout=delay*2)

            with contextlib.closing(get_socket()) as s:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

                self.assertEquals('Server is up', msg)

            pc.go()  # Once asserts are tested, we can shut the server down.

    def test_wait_server_down(self):
        """
        ``wait_server_up()`` will block a until port being listened is down.
        """
        delay = 0.01

        def serve():
            server = Server(message='Server is up')

            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            yield  # Wait until server is up.

            time.sleep(delay)
            server.shutdown()
            thread.join()

        with Process(target=serve) as pc:
            wait_server_up('localhost', 9000)
            start = time.time()

            pc.go()  # Once server is up, we can proceed with the test.

            wait_server_down('localhost', 9000)

            self.assertTrue(time.time() - start > delay)

    def test_wait_server_up_timeout(self):
        """
        ``wait_server_up()`` should wait for the time given in seconds as the
        ``timeout`` function.
        """
        timeout = 0.1
        with self.assertRaises(Exception):
            start = time.time()
            wait_server_up('localhost', 9000, timeout=timeout)

        now = time.time()

        self.assertTrue(timeout < now - start < 2*timeout)

    def test_wait_server_down_timeout(self):
        """
        ``wait_server_down()`` should wait for the time given in seconds as the
        ``timeout`` function.
        """
        timeout = 0.1
        with Server():
            with self.assertRaises(Exception):
                start = time.time()
                wait_server_down('localhost', 9000, timeout=timeout)

            now = time.time()

            self.assertTrue(timeout < now - start < 2*timeout)

    def test_wait_server_up_integer_timeout(self):
        """
        ``wait_server_up()`` should work with integer timeouts.
        """
        timeout = 1
        with self.assertRaises(Exception):
            start = time.time()
            wait_server_up('localhost', 9000, timeout=timeout)

        now = time.time()

        self.assertTrue(timeout < now - start < 2*timeout)

    def test_wait_server_down_integer_timeout(self):
        """
        ``wait_server_down()`` should work with integer timeouts.
        """
        timeout = 1
        with Server():
            with self.assertRaises(Exception):
                start = time.time()
                wait_server_down('localhost', 9000, timeout=timeout)

            now = time.time()

            self.assertTrue(timeout < now - start < 2*timeout)

    def test_wait_server_down_timeout_unmet(self):
        """
        ``wait_server_down()`` should not wait for the full timeout if the port
        is freed earlier.
        """
        timeout = 1
        start = time.time()
        wait_server_down('localhost', 9000, timeout=timeout)

        now = time.time()

        self.assertTrue(now - start < timeout)

    def test_wait_server_up_timeout_unmet(self):
        """
        ``wait_server_up()`` should not wait for the full timeout if the port
        is listening earliner.
        """
        timeout = 1
        with Server():
            start = time.time()
            wait_server_up('localhost', 9000, timeout=timeout)
            now = time.time()

        self.assertTrue(now - start < timeout)


load_tests = TestFinder(__name__, 'inelegant.net').load_tests

if __name__ == "__main__":
    unittest.main()
