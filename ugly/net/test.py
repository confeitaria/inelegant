import unittest

import multiprocessing
import socket
import contextlib
import time

from ugly.net import Server

class TestServer(unittest.TestCase):

    def test_server(self):
        """
        ``ugly.net.Server`` is a ` ``SocketServer.TCPServer`` `__ subclass.
        
        __ https://docs.python.org/2/library/socketserver.html#socketserver-tcpserver-example
        """
        def serve():
            server = Server(
                address='localhost', port=9000, message='Server is up'
            )
            server.handle_request()
            server.shutdown()

        process = multiprocessing.Process(target=serve)
        process.daemon = True
        process.start()
        time.sleep(0.01)

        with contextlib.closing(socket.socket()) as s:
            s.connect(('localhost', 9000))
            msg = s.recv(len('Server is up'))

            self.assertEquals('Server is up', msg)

        time.sleep(0.001)

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.net.net').load_tests

if __name__ == "__main__":
    unittest.main()
