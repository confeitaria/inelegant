import unittest
import doctest
import importlib
import inspect

class TestFinder(unittest.TestSuite):
    """
    ``UnitTestFinder`` is a test suite which receives as its arguments a list of
    modules to search for all tests inside them.
    """
    def __init__(self, *modules):
        unittest.TestSuite.__init__(self)

        for module in modules:
            if isinstance(module, basestring):
                module = importlib.import_module(module)

            self.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))
            try:
                self.addTest(doctest.DocTestSuite(module))
            except ValueError:
                pass

    def load_tests(self, loader, tests, pattern):
        """
        This method follows the ```load_tests() protocol`__. You can assign it
        (when bound) to ``load_tests`` inside a module and then the
        ``TestFinder`` will be the suite to be called.

        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """
        return self
