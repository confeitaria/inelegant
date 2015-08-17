try:
    import unittest2 as unittest
except:
    import unittest

class UnitTestFinder(unittest.TestSuite):
    """
    ``UnitTestFinder`` is a test suite which receives as its arguments a list of
    modules to search for all tests inside them.
    """
    pass
