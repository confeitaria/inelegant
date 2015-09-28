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

        caller_module = get_caller_module()

        for testable in testables:
            module, doctestable = get_sources(testable, caller_module)

            if module is not None:
                add_module(self, module)
            if doctestable is not None:
                add_doctest(self, doctestable, reference_module=caller_module)

    def load_tests(self, loader, tests, pattern):
        """
        This method follows the ```load_tests() protocol`__. You can assign it
        (when bound) to ``load_tests`` inside a module and then the
        ``TestFinder`` will be the suite to be called.

        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """
        return self

def get_sources(testable, reference_module=None):
    if reference_module is None:
        caller_frame = get_caller_module()

    if isinstance(testable, file):
        result = (None, testable.name)
    elif isinstance(testable, basestring):
        if testable == '.':
            result = (reference_module, reference_module)
        else:
            try:
                imported = importlib.import_module(testable)
                result = (imported, imported)
            except (ImportError, TypeError):
                result = (None, testable)
    elif inspect.ismodule(testable):
        result = (testable, testable)

    return result

def get_caller_module(stack_index=1):
    frame = sys._getframe(stack_index+1)

    return importlib.import_module(frame.f_globals['__name__'])

def add_doctest(suite, doctestable, reference_module, exclude_empty=False):
    if inspect.ismodule(doctestable):
        finder = doctest.DocTestFinder(exclude_empty=exclude_empty)
        doctest_suite = doctest.DocTestSuite(doctestable, test_finder=finder)
    else:
        if os.path.isabs(doctestable):
            path = doctestable
        else:
            module_dir = os.path.dirname(reference_module.__file__)
            path = os.path.join(module_dir, doctestable)

        doctest_suite = doctest.DocFileSuite(path, module_relative=False)

    suite.addTest(doctest_suite)

def add_module(suite, module):
    suite.addTest(
        unittest.defaultTestLoader.loadTestsFromModule(module)
    )
