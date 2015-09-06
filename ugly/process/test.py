import unittest

import contextlib
import time
import multiprocessing.connection

from ugly.process import ProcessContext

class TestProcessContext(unittest.TestCase):

    def test_process_context(self):
        """
        Blocks managed by ``ProcessContext`` should ensure a paralel process
        starts and, after the execution of the block, the process should have
        been finished.
        """
        def serve():
            time.sleep(0.001)

        with ProcessContext(target=serve) as pc:
            self.assertTrue(pc.process.is_alive())

        self.assertFalse(pc.process.is_alive())

    def test_process_context_serve(self):
        """
        To ensure  ``ProcessContext`` can start a server, here is a simple test
        doing that.
        """
        def serve():
            listener = multiprocessing.connection.Listener(('localhost', 9000))
            with contextlib.closing(listener):
                with contextlib.closing(listener.accept()) as connection:
                    connection.send('example')

        with ProcessContext(target=serve):
            client = multiprocessing.connection.Client(('localhost', 9000))
            with contextlib.closing(client) as client:
                self.assertEquals('example', client.recv())

    def test_process_context_finish_after_exception(self):
        """
        The process started by ``ProcessContext`` should be terminated if an
        exception happened in the ``with`` block.
        """
        def serve():
            time.sleep(60)

        try:
            start = time.time()
            with ProcessContext(target=serve) as pc:
                raise Exception()
        except:
            self.assertFalse(pc.process.is_alive())
            self.assertTrue(time.time() - start < 60)


from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.process.process').load_tests

if __name__ == "__main__":
    unittest.main()
