import unittest

import multiprocessing
import threading
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

    def test_wait_port_up_does_not_acquire_port(self):
        """
        ``wait_server_up()`` cannot impede other processes of capturing the
        port.
        """
        delay = 0.01
        start = time.time()

        def serve(condition, queue):
            try:
                time.sleep(delay)

                server = Server(message='Server is up')

                thread = threading.Thread(target=server.serve_forever)
                thread.start()

                condition.acquire()
                condition.wait()

                server.shutdown()
                thread.join()
            except Exception as e:
                queue.put(e)

        condition = multiprocessing.Condition()
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=serve, args=(condition, queue))
        process.start()

        wait_server_up('localhost', 9000, timeout=delay*2)

        with contextlib.closing(get_socket()) as s:
            s.connect(('localhost', 9000))
            msg = s.recv(len('Server is up'))

            self.assertEquals('Server is up', msg)

        condition.acquire()
        condition.notify_all()
        condition.release()

        process.join()

        if not queue.empty():
            raise queue.get()

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.net.net').load_tests

if __name__ == "__main__":
    unittest.main()
