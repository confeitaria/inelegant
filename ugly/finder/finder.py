import unittest
import doctest
import importlib
import inspect
import sys
import os

class TestFinder(unittest.TestSuite):
    """
    ``UnitTestFinder`` is a test suite which receives as its arguments a list of
    modules to search for all tests inside them.
    """
    def __init__(self, *testables):
        unittest.TestSuite.__init__(self)

        for testable in testables:
            if isinstance(testable, file):
                self.add_doctests(testable.name)
            elif isinstance(testable, basestring):
                if testable == '.':
                    caller = sys._getframe(1)
                    name = caller.f_globals['__name__']
                else:
                    name = testable

                try:
                    module = importlib.import_module(name)
                    self.add_tests_from_module(module)
                except ImportError:
                    self.add_doctests(name)
            else:
                self.add_tests_from_module(testable)

    def add_doctests(self, file_name):
        module_relative = not file_name.startswith(os.sep)
        self.addTest(
            doctest.DocFileSuite(file_name, module_relative=module_relative)
        )

    def add_tests_from_module(self, module):
        self.addTest(
            unittest.defaultTestLoader.loadTestsFromModule(module)
        )
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
