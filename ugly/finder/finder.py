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
    def __init__(self, *modules):
        unittest.TestSuite.__init__(self)

        for module in modules:
            if isinstance(module, file):
                self.add_doctests(module.name)
            elif isinstance(module, basestring):
                if module == '.':
                    caller = sys._getframe(1)
                    name = caller.f_globals['__name__']
                else:
                    name = module

                module = importlib.import_module(name)

                self.add_tests_from_module(module)
            else:
                self.add_tests_from_module(module)

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
