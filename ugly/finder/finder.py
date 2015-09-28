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
        self.caller_module = caller.f_globals['__name__']

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
                module = importlib.import_module(self.caller_module)
                module_dir = os.path.dirname(module.__file__)
                path = os.path.join(module_dir, doctestable)

            suite = doctest.DocFileSuite(path, module_relative=False)

        self.addTest(suite)

    def add_module(self, module):
        self.addTest(
            unittest.defaultTestLoader.loadTestsFromModule(module)
        )

    def get_sources(self, testable):
        doctestable = None
        module = None
        if isinstance(testable, file):
            doctestable = testable.name
        elif isinstance(testable, basestring):
            if testable == '.':
                name = self.caller_module
            else:
                name = testable

            try:
                module = importlib.import_module(name)
                doctestable = module
            except (ImportError, TypeError):
                doctestable = name
        elif inspect.ismodule(testable):
            module = testable
            doctestable = module

        return module, doctestable

    def load_tests(self, loader, tests, pattern):
        """
        This method follows the ```load_tests() protocol`__. You can assign it
        (when bound) to ``load_tests`` inside a module and then the
        ``TestFinder`` will be the suite to be called.

        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """
        return self
