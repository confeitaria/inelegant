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
            module = get_module(testable, reference_module=caller_module)
            doctestable = get_doctestable (
                testable, reference_module=caller_module
            )

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

def get_module(testable, reference_module=None):
    if reference_module is None:
        reference_module = get_caller_module()

    module = None

    if isinstance(testable, basestring):
        if testable == '.':
            module = reference_module
        else:
            try:
                module = importlib.import_module(testable)
            except (ImportError, TypeError):
                module = None
    elif inspect.ismodule(testable):
        module = testable

    return module

def get_doctestable(testable, reference_module=None):
    if reference_module is None:
        reference_module = get_caller_module()

    doctestable = None

    if isinstance(testable, file):
        doctestable = testable.name
    elif isinstance(testable, basestring):
        if testable == '.':
            doctestable = reference_module
        else:
            doctestable = get_module(testable, reference_module)
            if doctestable is None:
                doctestable = testable
    elif inspect.ismodule(testable):
        doctestable = testable

    return doctestable

def get_caller_module(stack_index=1):
    """
    ``get_caller_module()`` returns a module from the stack. One can give it the
    ``stack_index`` arg - an integer defining the position at the call stack
    from which to get the module.

    So, if a module ``m1`` calls a function ``f`` from module ``m2``, ``f``
    calls ``g`` from ``m3`` and ``g`` calls ``get_caller_module()`` with stack
    index 1, then ``m2`` is returned (since it calls ``g``). If the stack index
    were 2, then ``m2`` would returned, and 3 as the stack index would return
    ``m1``.

    By default, the value of the stack index is 1 - it will return the module
    which called the function that called ``get_caller_module()``.
    """
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
