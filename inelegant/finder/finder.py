#
# Copyright 2015, 2016 Adam Victor Brandizzi
#
# This file is part of Inelegant.
#
# Inelegant is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Inelegant is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Inelegant.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import doctest
import importlib
import inspect
import sys
import os

from inelegant.module import get_caller_module

class TestFinder(unittest.TestSuite):
    """
    ``TestFinder`` is a subclass of ``unittest.TestSuite``. It receives modules,
    modules names and file paths as its arguments. It will look for subclasses
    of ``unittest.TestCase`` and ``unittest.TestSuite`` from each module it
    receives. It will also look for doctests in the docstrings of the functions
    and classes from the module. If a file path is given to it, then it will
    look for doctests inside it.

    Loading test cases
    ------------------

    If we have the test case below...

    ::

    >>> class SomeTestCase(unittest.TestCase):
    ...     def test1(self):
    ...         self.assertEquals(1, 1)
    ...     def testFail(self):
    ...         self.assertEquals(1, 0)
    ...     def testError(self):
    ...         self.assertEquals(1, 1/0)

    ...in a module, and the module is given to the finder, then all of these
    tests will be available in the finder::

    >>> from inelegant.module import installed_module
    >>> with installed_module('t', scope={'SomeTestCase': SomeTestCase}) as t:
    ...     finder = TestFinder(t)
    ...     finder.countTestCases()
    3

    It also works if one gives the module name instead of the module itself::

    >>> with installed_module('t', scope={'SomeTestCase': SomeTestCase}):
    ...     finder = TestFinder('t')
    ...     finder.countTestCases()
    3

    All other methods from ``unittest.TestSuite`` are available as well.

    Loading docstrings
    ------------------

    If a module containing docstrings with doctests is given to the finder then
    a the doctest cases will also be available. So, if we had such a class::

    >>> class Point(object):
    ...     '''
    ...     Is a point:
    ...
    ...     >>> p = Point(2, 3)
    ...     >>> p.x
    ...     2
    ...     >>> p.y
    ...     3
    ...     '''
    ...     def __init__(self, x, y):
    ...         self.x = x
    ...         self.y = y
    ...     def distance(self, point):
    ...         '''
    ...         Distance to other point:
    ...
    ...         >>> Point(0, 0).distance(Point(2, 3)
    ...         5.0
    ...         '''
    ...         return ((self.x-point.x)**2 + (self.y-point.y)**2)**(1/2)

    ...and its module is given to the finder, the finder will have two test
    cases - one for the class docstring and other for the method docstring::

    >>> with installed_module('point', defs=[Point]) as p:
    ...     finder = TestFinder(p)
    ...     finder.countTestCases()
    2

    Loading files
    -------------

    Doctests can be added to arbitrary text files as well, and ``TestFinder``
    can also load them. Given a file as the one below::

    >>> import tempfile
    >>> content = '''
    ...     >>> 3+3
    ...     6
    ... '''
    >>> _, path = tempfile.mkstemp()
    >>> with open(path, 'w') as f:
    ...     f.write(content)

    ...one just needs to give its path to the finder to have the doctests loaded
    as test cases::

    >>> finder = TestFinder(path)
    >>> finder.countTestCases()
    1

    The nicest thing of it all, however, is that one can give all these options,
    to the finder at once::

    >>> with installed_module('t', defs=[SomeTestCase]),\\
    ...         installed_module('point', defs=[Point]) as p:
    ...     finder = TestFinder('t', p, path)
    ...     finder.countTestCases()
    6
    >>> import os
    >>> os.remove(path)
    """
    def __init__(self, *testables):
        unittest.TestSuite.__init__(self)

        try:
            caller_module = get_caller_module()
        except:
            caller_module = importlib.import_module('__main__')

        for testable in testables:
            module = get_module(testable)
            doctestable = get_doctestable(testable)

            if module is not None:
                add_module(self, module)
            if doctestable is not None:
                add_doctest(self, doctestable, reference_module=caller_module)

    def load_tests(self, loader, tests, pattern):
        """
        This is, basically, an implementation of the ```load_tests()
        protocol`__. You can assign it (when bound) to ``load_tests`` inside a
        module and then the ``TestFinder`` will be the suite to be called.

        For example, suppose we have the following classes

        >>> class TestCase1(unittest.TestCase):
        ...    def test_fail1(self):
        ...        self.fail('TestCase1')
        >>> class TestCase2(unittest.TestCase):
        ...    def test_fail2(self):
        ...        self.fail('TestCase1')

        If we add them to two different modules, but then create a finder with
        the first one and set its bound ``load_tests()`` into the second one,
        then the second module will only "publish" the cases of the first one::

        >>> from inelegant.module import installed_module
        >>> with installed_module('t1', defs=[TestCase1]) as t1, \\
        ...        installed_module('t2', defs=[TestCase2]) as t2:
        ...     t2.load_tests = TestFinder(t1).load_tests
        ...     loader = unittest.TestLoader()
        ...     suite = loader.loadTestsFromModule(t2)
        ...     # doctest: +ELLIPSIS
        ...     _ = unittest.TextTestRunner(stream=sys.stdout).run(suite)
        F
        ======================================================================
        FAIL: test_fail1 (t1.TestCase1)
        ----------------------------------------------------------------------
        Traceback (most recent call last):
          ...
        AssertionError: TestCase1
        <BLANKLINE>
        ----------------------------------------------------------------------
        Ran 1 test in ...s
        <BLANKLINE>
        FAILED (failures=1)


        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """
        return self

def get_module(testable):
    """
    ``get_module()`` can receive a module or a string. If it receives a module,
    the module is returned::

    >>> import inelegant.finder.test
    >>> get_module(inelegant.finder.test) # doctest: +ELLIPSIS
    <module 'inelegant.finder.test' ...>

    If it receives a string, it is supposed to be the name of a module. Then the
    module is returned::

    ::

    >>> get_module('inelegant.net.test') # doctest: +ELLIPSIS
    <module 'inelegant.net.test' ...>
    """

    module = None

    if inspect.ismodule(testable):
        module = testable
    elif isinstance(testable, basestring):
        try:
            module = importlib.import_module(testable)
        except (ImportError, TypeError):
            module = None

    return module

def get_doctestable(testable):
    """
    Given a "testable" argument, returns something that can be run by
    ``doctest`` - a "doctestable."

    Doctests can be found in modules (as docstrings) and in text files. This
    function can receive, then, a module, a string or a file object, and returns
    either a module or a path to a file.

    Retrieving modules
    ------------------

    If the function receives a module, it merely returns the module.

    >>> from inelegant.module import installed_module
    >>> with installed_module('m') as m:
    ...     get_doctestable(m) # doctest: +ELLIPSIS
    <module 'm' ...>

    If it receives a string, it can be one of two things: a module name or a
    file path. If it is a module name, then the function returns the module::

    >>> with installed_module('m') as m:
    ...     get_doctestable('m') # doctest: +ELLIPSIS
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
    doctestable = None

    if inspect.ismodule(testable):
        doctestable = testable
    elif isinstance(testable, file):
        doctestable = testable.name
    elif isinstance(testable, basestring):
        doctestable = get_module(testable)
        if doctestable is None:
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
