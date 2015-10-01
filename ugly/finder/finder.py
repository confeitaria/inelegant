import unittest
import doctest
import importlib
import inspect
import sys
import os

from ugly.module import get_caller_module

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
    """
    ``get_module()`` can receive a module or a string. If it receives a module,
    the module is returned::

    >>> import ugly.finder.test
    >>> get_module(ugly.finder.test) # doctest: +ELLIPSIS
    <module 'ugly.finder.test' ...>

    If it receives a string, it is supposed to be the name of a module. Then the
    module is returned::

    ::

    >>> get_module('ugly.net.test') # doctest: +ELLIPSIS
    <module 'ugly.net.test' ...>

    The "dot module"
    ----------------

    However, if a string containg only a period (``'.'``) is given to the
    function, then the function will return the module which called the
    function::

    >>> get_module('.') # doctest: +ELLIPSIS
    <module 'ugly.finder.finder' ...>

    The reference module
    --------------------

    Sometimes, however, you many want to return a different "dot module." For
    example, consider the function below::

    >>> def get_current_module():
    ...     return get_module('.')

    If it is imported called from a module ``m1``, it will return its original
    module::

    >>> from ugly.module import installed_module
    >>> scope = {'get_current_module': get_current_module}
    >>> code = 'print get_current_module()'
    >>> with installed_module('m', scope=scope, code=code) as m:
    ...     pass # doctest: +ELLIPSIS
    <module 'ugly.finder.finder' ...>

    What we want, however, is the module where ``get_current_module()`` was
    called. In this case, can pass it as the ``reference_module`` argument::

    >>> def get_current_module():
    ...     module = get_caller_module(1)
    ...     return get_module('.', reference_module=module)

    Now it should work::

    >>> scope = {'get_current_module': get_current_module}
    >>> with installed_module('m', scope=scope, code=code) as m:
    ...     pass # doctest: +ELLIPSIS
    <module 'm' ...>
    """
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
    """
    Given a "testable" argument, returns something that can be run by
    ``doctest`` - a "doctestable."

    Doctests can be found in modules (as docstrings) and in text files. This
    function can receive, then, a module, a string or a file object, and returns
    either a module or a path to a file.

    Retrieving modules
    ------------------

    If the function receives a module, it merely returns the module.

    >>> from ugly.module import installed_module
    >>> with installed_module('m') as m:
    ...     get_doctestable(m) # doctest: +ELLIPSIS
    <module 'm' ...>

    If it receives a string, it can be one of two things: a module name or a
    file path. If it is a module name, then the function returns the module::

    >>> with installed_module('m') as m:
    ...     get_doctestable('m') # doctest: +ELLIPSIS
    <module 'm' ...>

    The "dot module"
    ----------------

    The function can also receive the string ``"."``. In this case, it will
    return the module that called it::

    >>> scope = {'get_doctestable': get_doctestable}
    >>> code = "print get_doctestable('.')"
    >>> with installed_module('m', code=code, scope=scope) as m:
    ...     pass # doctest: +ELLIPSIS
    <module 'm' ...>

    However, if the function is called from another function, it may not be the
    desired outcome. For example, consider de function below::

    >>> def get_current_doctestable():
    ...     return get_doctestable('.')

    Were it called inside a module, one would expect it to return the calling
    module, but this does not happen::

    >>> scope = {'get_current_doctestable': get_current_doctestable}
    >>> code = "print get_current_doctestable()"
    >>> with installed_module('m', code=code, scope=scope) as m:
    ...     pass # doctest: +ELLIPSIS
    <module 'ugly.finder.finder' ...>

    The new function adds a new call to the frame stack, so the module where
    ``get_current_doctestable()`` is defined ends up being returned. If we
    want the dot module to return a different module, we have a solution,
    however: just set the ``reference_module`` argument::

    >>> def get_current_doctestable():
    ...     module = get_caller_module(1)
    ...     return get_doctestable('.', reference_module=module)
    >>> scope = {'get_current_doctestable': get_current_doctestable}
    >>> with installed_module('m', code=code, scope=scope) as m:
    ...     pass # doctest: +ELLIPSIS
    <module 'm' ...>

    Retrieving files
    ----------------

    If ``get_doctestable()`` receives a file object, then it will return the
    path to the file::

    >>> import os, os.path,  tempfile
    >>> _, path = tempfile.mkstemp()
    >>> doctestable = get_doctestable(open(path))
    >>> os.path.samefile(path, doctestable)
    True
    >>> os.remove(path)

    If it receives a string, and the sting is not a module name, then it is
    assumed to be a file path, so it is returned as well::

    >>> get_doctestable('/tmp/doctest.txt')
    '/tmp/doctest.txt'
    """
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

def add_doctest(suite, doctestable, reference_module, exclude_empty=False):
    """
    Given a doctestable, add a test case to run it into the given suite.

    But, what is a doctestable?

    Well, a doctestable is an object that can contain doctests. It is either a
    module, a file or a path to a file.

    If the doctestable is a module, a file object or an absolute path, its
    behavior can be very predictable: it will load the docstrings from the
    module or the content of the file. However, if it is a relative path, then
    the file path is relative to the given module given as ``reference_module``.
    """
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
    """
    Add all test cases and test suites from the given module into the given
    suite.
    """
    suite.addTest(
        unittest.defaultTestLoader.loadTestsFromModule(module)
    )
