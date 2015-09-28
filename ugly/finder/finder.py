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
        caller = sys._getframe(1)
        self.caller_module = importlib.import_module(
            caller.f_globals['__name__']
        )

        for testable in testables:
            module, doctestable = self.get_sources(testable)

            if module is not None:
                self.add_module(module)
            if doctestable is not None:
                self.add_doctest(doctestable)

    def add_doctest(self, doctestable):
        if inspect.ismodule(doctestable):
            suite = doctest.DocTestSuite(
                doctestable, test_finder=self.doctest_finder
            )
        else:
            if os.path.isabs(doctestable):
                path = doctestable
            else:
                module_dir = os.path.dirname(self.caller_module.__file__)
                path = os.path.join(module_dir, doctestable)

            suite = doctest.DocFileSuite(path, module_relative=False)

        self.addTest(suite)

    def add_module(self, module):
        self.addTest(
            unittest.defaultTestLoader.loadTestsFromModule(module)
        )

    def get_sources(self, testable):
        if isinstance(testable, file):
            result = (None, testable.name)
        elif isinstance(testable, basestring):
            if testable == '.':
                result = self.caller_module, self.caller_module
            else:
                try:
                    imported = importlib.import_module(testable)
                    result = (imported, imported)
                except (ImportError, TypeError):
                    result = (None, testable)
        elif inspect.ismodule(testable):
            result = (testable, testable)

        return result

    def load_tests(self, loader, tests, pattern):
        """
        This method follows the ```load_tests() protocol`__. You can assign it
        (when bound) to ``load_tests`` inside a module and then the
        ``TestFinder`` will be the suite to be called.

        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """
        return self
