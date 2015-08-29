import unittest

import multiprocessing
import socket
import contextlib
import time
import errno

from ugly.net import Server

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

        with contextlib.closing(socket.socket()) as s:
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
            with contextlib.closing(socket.socket()) as s:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

                self.assertEquals('Server is up', msg)

        s = socket.socket()
        s.settimeout(0.00001)
        with contextlib.closing(s) as s:
            with self.assertRaises(socket.error) as a:
                s.connect(('localhost', 9000))
                msg = s.recv(len('Server is up'))

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.net.net').load_tests

if __name__ == "__main__":
    unittest.main()
