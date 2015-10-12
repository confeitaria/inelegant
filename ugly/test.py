import unittest
import os, os.path

import ugly.finder.test
import ugly.module.test
import ugly.net.test
import ugly.process.test

from ugly.finder import TestFinder

readme_path = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    'readme.rst'
)

load_tests = TestFinder(
    readme_path,
    ugly.finder.test,
    ugly.module.test,
    ugly.net.test,
    ugly.process.test
).load_tests

if __name__ == "__main__":
    unittest.main()
