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
        self.doctest_finder = doctest.DocTestFinder(exclude_empty=False)

        for testable in testables:
            doctestable = None
            module = None
            if isinstance(testable, file):
                doctestable = testable.name
            elif isinstance(testable, basestring):
                if testable == '.':
                    caller = sys._getframe(1)
                    name = caller.f_globals['__name__']
                else:
                    name = testable

                try:
                    module = importlib.import_module(name)
                    doctestable = module
                except ImportError:
                    doctestable = name
            elif inspect.ismodule(testable):
                module = testable
                doctestable = module

            if module is not None:
                self.add_tests_from_module(module)
            if doctestable is not None:
                self.add_doctests(doctestable)

    def add_doctests(self, file_name):
        if inspect.ismodule(file_name):
            suite = doctest.DocTestSuite(
                file_name, test_finder=self.doctest_finder
            )
        else:
            module_relative = not file_name.startswith(os.sep)
            suite = doctest.DocFileSuite(
                file_name, module_relative=module_relative
            )

        self.addTest(suite)

    def add_tests_from_module(self, module):
        self.addTest(
            unittest.defaultTestLoader.loadTestsFromModule(module)
        )

    def load_tests(self, loader, tests, pattern):
        """
        This method follows the ```load_tests() protocol`__. You can assign it
        (when bound) to ``load_tests`` inside a module and then the
        ``TestFinder`` will be the suite to be called.

        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """
        return self
