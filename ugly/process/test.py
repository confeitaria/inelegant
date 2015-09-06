import unittest

import contextlib
import time

from ugly.process import ProcessContext

class TestProcessContext(unittest.TestCase):

    def test_process_context(self):
        """
        Blocks managed by ``ProcessContext`` should ensure a paralel process
        starts and, after the execution of the block, the process should have
        been finished.
        """
        def serve():
            time.sleep(0.01)

        with ProcessContext(target=serve) as pc:
            self.assertTrue(pc.process.is_alive())

        self.assertFalse(pc.process.is_alive())

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.process.process').load_tests

if __name__ == "__main__":
    unittest.main()
