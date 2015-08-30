import unittest

import ugly.finder.test
import ugly.module.test
import ugly.net.test

from ugly.finder import TestFinder

load_tests = TestFinder(
    ugly.finder.test,
    ugly.module.test,
    ugly.net.test
).load_tests

if __name__ == "__main__":
    unittest.main()
