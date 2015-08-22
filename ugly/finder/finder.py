try:
    import unittest2 as unittest
except:
    import unittest

import inspect

class UnitTestFinder(unittest.TestSuite):
    """
    ``UnitTestFinder`` is a test suite which receives as its arguments a list of
    modules to search for all tests inside them.
    """
    def __init__(self, *modules):
        unittest.TestSuite.__init__(self)

        for module in modules:
            self.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))

