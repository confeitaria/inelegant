import unittest

import contextlib
import time
import multiprocessing.connection

from ugly.process import ContextualProcess

class TestContextualProcess(unittest.TestCase):

    def test_process_context(self):
        """
        Blocks managed by ``ContextualProcess`` should ensure a paralel process
        starts and, after the execution of the block, the process should have
        been finished.
        """
        def serve():
            time.sleep(0.001)

        with ContextualProcess(target=serve) as pc:
            self.assertTrue(pc.is_alive())

        self.assertFalse(pc.is_alive())

    def test_serve(self):
        """
        To ensure ``ContextualProcess`` can start a server, here is a simple
        test doing that.
        """
        def serve():
            listener = multiprocessing.connection.Listener(('localhost', 9001))
            with contextlib.closing(listener):
                with contextlib.closing(listener.accept()) as connection:
                    connection.send('example')

        with ContextualProcess(target=serve):
            client = multiprocessing.connection.Client(('localhost', 9001))
            with contextlib.closing(client) as client:
                self.assertEquals('example', client.recv())

    def test_terminate_after_exception(self):
        """
        The process started by ``ContextualProcess`` should be terminated if an
        exception happened in the ``with`` block.
        """
        def serve():
            time.sleep(60)

        try:
            start = time.time()
            with ContextualProcess(target=serve) as pc:
                raise Exception()
        except:
            self.assertFalse(pc.is_alive())
            self.assertTrue(time.time() - start < 60)

    def test_save_process_exception(self):
        """
        If an exception happens in the spawned process, ``ContextualProcess``
        should provide it to the original process.
        """
        def serve():
            raise AssertionError('Actually, it is expected')

        with ContextualProcess(target=serve) as pc:
            pass

        self.assertIsInstance(pc.exception, AssertionError)
        self.assertEquals('Actually, it is expected', pc.exception.args[0])

    def test_send_receive_data(self):
        """
        Blocks managed by ``ContextualProcess`` should ensure a paralel process
        starts and, after the execution of the block, the process should have
        been finished.
        """
        def serve(value):
            value = yield value
            yield value

        with ContextualProcess(target=serve, args=(1,)) as pc:
            value = pc.get()
            self.assertEquals(1, value)

            value = pc.send(2)
            value = pc.get()
            self.assertEquals(2, value)

            pc.go()

    def test_get_result(self):
        """
        ``ContextualProcess`` should store the returned value (if the function
        is not a generator function).
        """
        def serve():
            return 1

        with ContextualProcess(target=serve) as pc:
            pass

        self.assertEquals(1, pc.result)

    def test_force_terminate(self):
        """
        If ``force_terminate`` is set to ``True`` at ``ContextualProcess``
        initialization, then the process should be forcefully terminated after
        the block finishes.
        """
        def serve():
            while True: pass

        with ContextualProcess(target=serve, force_terminate=True) as pc:
            pass

        self.assertFalse(pc.is_alive())

    def test_raise_child_error(self):
        """
        If ``raise_child_error`` is set to ``True`` at ``ContextualProcess``
        initialization and an untreated exception finished the child process,
        then this exception should be re-raised after the block.
        """
        def serve():
            raise AssertionError('Actually, it is expected')

        with self.assertRaises(AssertionError) as e:
            with ContextualProcess(target=serve, raise_child_error=True) as pc:
                pass

            self.assertEquals('Actually, it is expected', e.args[0])

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.process.process').load_tests

if __name__ == "__main__":
    unittest.main()
