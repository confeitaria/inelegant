import unittest

import contextlib
import time
import multiprocessing.connection

from ugly.process import Process

class TestProcess(unittest.TestCase):

    def test_process_context(self):
        """
        Blocks managed by ``Process`` should ensure a paralel process starts
        and, after the execution of the block, the process should have been
        finished.
        """
        def serve():
            time.sleep(0.001)

        with Process(target=serve) as pc:
            self.assertTrue(pc.is_alive())

        self.assertFalse(pc.is_alive())

    def test_serve(self):
        """
        To ensure ``Process`` can start a server, here is a simple test doing
        that.
        """
        def serve():
            listener = multiprocessing.connection.Listener(('localhost', 9001))
            with contextlib.closing(listener):
                with contextlib.closing(listener.accept()) as connection:
                    connection.send('example')

        with Process(target=serve):
            client = multiprocessing.connection.Client(('localhost', 9001))
            with contextlib.closing(client) as client:
                self.assertEquals('example', client.recv())

    def test_terminate_after_exception(self):
        """
        The process started by ``Process`` should be terminated if an exception
        happened in the ``with`` block.
        """
        def serve():
            time.sleep(60)

        try:
            start = time.time()
            with Process(target=serve) as p:
                raise Exception()
        except:
            self.assertFalse(p.is_alive())
            self.assertTrue(time.time() - start < 60)

    def test_save_process_exception(self):
        """
        If an exception happens in the spawned process, ``Process`` should
        provide it to the original process.
        """
        def serve():
            raise AssertionError('Actually, it is expected')

        with Process(target=serve) as p:
            pass

        self.assertIsInstance(p.exception, AssertionError)
        self.assertEquals('Actually, it is expected', p.exception.args[0])

    def test_send_receive_data(self):
        """
        Blocks managed by ``Process`` should ensure a paralel process starts
        and, after the execution of the block, the process should have been
        finished.
        """
        def serve(value):
            value = yield value
            yield value

        with Process(target=serve, args=(1,)) as p:
            value = p.get()
            self.assertEquals(1, value)

            value = p.send(2)
            value = p.get()
            self.assertEquals(2, value)

            p.go()

    def test_get_result(self):
        """
        ``Process`` should store the returned value (if the function is not a
        generator function).
        """
        def serve():
            return 1

        with Process(target=serve) as p:
            pass

        self.assertEquals(1, p.result)

    def test_force_terminate(self):
        """
        If ``force_terminate`` is set to ``True`` at ``Process`` initialization,
        then the process should be forcefully terminated after the block
        finishes.
        """
        def serve():
            while True: pass

        with Process(target=serve, force_terminate=True) as p:
            pass

        self.assertFalse(p.is_alive())

    def test_raise_child_error(self):
        """
        If ``raise_child_error`` is set to ``True`` at ``Process``
        initialization and an untreated exception finished the child process,
        then this exception should be re-raised after the block.
        """
        def serve():
            raise AssertionError('Actually, it is expected')

        with self.assertRaises(AssertionError) as e:
            with Process(target=serve, raise_child_error=True) as p:
                pass

            self.assertEquals('Actually, it is expected', e.args[0])

    def test_send_receive_data_fails_on_non_generator_function(self):
        """
        If one tries to send to or receive data from a ``Process`` that received
        a non-generator function, those calls should fail.
        """
        def serve():
            time.sleep(0.001)

        with Process(target=serve) as p:
            with self.assertRaises(ValueError):
                value = p.get()

            with self.assertRaises(ValueError):
                value = p.send(2)

            with self.assertRaises(ValueError):
                p.go()


    def test_get_result_after_join(self):
        """
        If ``Process`` is joined, the target's returned value should be
        available provided the timeout is not reached.
        """
        def serve():
            time.sleep(0.001)
            return 1

        p = Process(target=serve)
        p.start()

        self.assertIsNone(p.result)

        p.join()

        self.assertEquals(1, p.result)


from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.process.process').load_tests

if __name__ == "__main__":
    unittest.main()
