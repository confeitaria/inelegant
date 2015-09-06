import unittest

import ugly.finder.test
import ugly.module.test
import ugly.net.test
import ugly.process.test

from ugly.finder import TestFinder

load_tests = TestFinder(
    ugly.finder.test,
    ugly.module.test,
    ugly.net.test,
    ugly.process.test
).load_tests

if __name__ == "__main__":
    unittest.main()
