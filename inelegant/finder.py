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
import itertools
import sys
import os

from inelegant.module import get_caller_module


class TestFinder(unittest.TestSuite):
    """
    ``TestFinder`` is a subclass of ``unittest.TestSuite``. It receives
    modules, modules names and file paths as its arguments. It will look for
    subclasses of ``unittest.TestCase`` and ``unittest.TestSuite`` from each
    module it receives. It will also look for doctests in the docstrings of the
    functions and classes from the module. If a file path is given to it, then
    it will look for doctests inside it.

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


    Ignoring test cases
    -------------------

    Sometimes we may not want to load a specific test case. In these cases, we
    can pass the test case's classes to be ignored to the named-only ``skip``
    argument::

    >>> class TestCase1(unittest.TestCase):
    ...     def testFail(self):
    ...         self.assertEquals(1, 0)
    >>> class TestCase2(unittest.TestCase):
    ...     def testError(self):
    ...         self.assertEquals(1, 1/0)
    >>> with installed_module('t1', defs=[TestCase1, TestCase2]) as t1:
    ...     finder = TestFinder(t1)
    ...     finder.countTestCases()
    2
    >>> with installed_module('t1', defs=[TestCase1, TestCase2]) as t1:
    ...     finder = TestFinder(t1, skip=[TestCase2])
    ...     finder.countTestCases()
    1

    If only one class is to be ignored, it can be passed directly

    >>> with installed_module('t1', defs=[TestCase1, TestCase2]) as t1:
    ...     finder = TestFinder(t1, skip=TestCase2)
    ...     finder.countTestCases()
    1

    It is very useful when a base test case is to be extended with necessary
    methods::

    >>> class TestMultiplier(unittest.TestCase):
    ...        def test_add(self):
    ...            m = self.get_multiplier()
    ...            self.assertEquals(4, m(2, 2))

    This way, it can test different implementations::

    >>> def mul1(a, b):
    ...        return a*b
    >>> def mul2(a, b):
    ...        return sum([a]*b)
    >>> class TestMul1(TestMultiplier):
    ...        def get_multiplier(self):
    ...            return mul1
    >>> class TestMul2(TestMultiplier):
    ...        def get_multiplier(self):
    ...            return mul2

    Naturally, we do not want to run tests from the base class. However, it is
    usually imported into the modules that are going to extend it, causing
    errors::

    >>> runner = unittest.TextTestRunner(stream=sys.stdout)
    >>> with installed_module('tm', defs=[TestMultiplier, TestMul1, TestMul2]):
    ...     finder = TestFinder('tm')
    ...     _ = runner.run(finder) # doctest: +ELLIPSIS
    ..E
    ======================================================================
    ERROR: test_add (tm.TestMultiplier)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      ...
    AttributeError: 'TestMultiplier' object has no attribute 'get_multiplier'
    ...
    Ran 3 tests in ...
    ...
    FAILED (errors=1)

    Here the ``skip`` argument helps::

    >>> with installed_module('tm', defs=[TestMultiplier, TestMul1, TestMul2]):
    ...     finder = TestFinder('tm', skip=[TestMultiplier])
    ...     _ = runner.run(finder) # doctest: +ELLIPSIS
    ..
    ----------------------------------------------------------------------
    Ran 2 tests in ...
    <BLANKLINE>
    OK

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
    can also load them. Given the example below one just needs to give its path
    to the finder to have the doctests loaded as test cases::

    >>> from inelegant.fs import temp_file as tempfile
    >>> content = '''
    ...     >>> 3+3
    ...     6
    ... '''
    >>> with tempfile(content=content) as path:
    ...     finder = TestFinder(path)
    ...     finder.countTestCases()
    1

    The nicest thing of it all, however, is that one can give all these
    options, to the finder at once::

    >>> with tempfile(content=content) as path:
    ...     with installed_module('t', defs=[SomeTestCase]),\\
    ...             installed_module('point', defs=[Point]) as p:
    ...         finder = TestFinder('t', p, path)
    ...         finder.countTestCases()
    6
    """
    def __init__(self, *testables, **kwargs):
        unittest.TestSuite.__init__(self)

        skip = kwargs.get('skip', None)

        try:
            caller_module = get_caller_module()
        except:
            caller_module = importlib.import_module('__main__')

        for testable in testables:
            module = get_module(testable)
            doctestable = get_doctestable(testable)

            if module is not None:
                add_module(self, module, skip=skip)
            if doctestable is not None:
                module_path = getattr(caller_module, '__file__', '.')
                module_dir = os.path.dirname(module_path)
                add_doctest(self, doctestable, working_dir=module_dir)

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

    >>> import inelegant.test.finder
    >>> get_module(inelegant.test.finder) # doctest: +ELLIPSIS
    <module 'inelegant.test.finder' ...>

    If it receives a string, it is supposed to be the name of a module. Then
    the module is returned::

    ::

    >>> get_module('inelegant.test.net') # doctest: +ELLIPSIS
    <module 'inelegant.test.net' ...>
    """

    module = None

    if inspect.ismodule(testable):
        module = testable
    elif isinstance(testable, basestring):
        try:
            module = importlib.import_module(testable)
        except ImportError:
            if len(get_exc_frames()) > 2:
                raise
            module = None
        except TypeError:
            module = None

    return module


def get_exc_frames():
    """
    Return the list of frames that were executed from the raised exception
    until the current function::

    >>> try:
    ...     raise Exception()
    ... except:
    ...     get_exc_frames()  # doctest: +ELLIPSIS
    [<frame object at ...>]

    So, if the exception was raised from a function, its frame will be present
    in the list::

    >>> def raise_exception():
    ...    raise Exception()
    >>> try:
    ...     raise_exception()
    ... except:
    ...     get_exc_frames()  # doctest: +ELLIPSIS
    [<frame object at ...>, <frame object at ...>]
    """
    traceback = sys.exc_info()[2]
    frame_list = []

    while traceback:
        frame_list.append(traceback.tb_frame)
        traceback = traceback.tb_next

    return frame_list


def get_doctestable(testable):
    """
    Given a "testable" argument, returns something that can be run by
    ``doctest`` - a "doctestable."

    Doctests can be found in modules (as docstrings) and in text files. This
    function can receive, then, a module, a string or a file object, and
    returns either a module or a path to a file.

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

    >>> from inelegant.fs import temp_file as tempfile
    >>> import os, os.path
    >>> with tempfile() as path:
    ...     doctestable = get_doctestable(open(path))
    ...     os.path.samefile(path, doctestable)
    True

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


def add_doctest(suite, doctestable, working_dir=None, exclude_empty=False):
    r"""
    Given a doctestable, add a test case to run it into the given suite.

    But, what is a doctestable?

    Well, a doctestable is an object that can contain doctests. It is either a
    module or a path to a file.

    Loading modules
    ===============

    If the doctestable is a module, it will load the docstrings from the module
    definitions into the test suite::

    >>> class Test(object):
    ...     '''
    ...     >>> 2+2
    ...     4
    ...     '''
    >>> suite = unittest.TestSuite()
    >>> from inelegant.module import installed_module
    >>> with installed_module('m', defs=[Test]) as m:
    ...     add_doctest(suite, m)
    ...     suite.countTestCases()
    1

    Loading absolute paths
    ======================

    Paths to files are also valid doctestables. The behavior, however, depends
    whether the path is absolute or relative. If the doctestable is an absolute
    path, then it will read the content as doctest and add a test running it
    into the suite::

    ::

    >>> from inelegant.fs import temp_file as tempfile
    >>> with tempfile(content='>>> 2+2\n4') as docfile:
    ...     os.path.isabs(docfile)
    ...     suite = unittest.TestSuite()
    ...     add_doctest(suite, docfile)
    ...     suite.countTestCases()
    True
    1

    Loading relative paths
    ======================

    If it is a relative path, then it should be relative to the current path
    by default::

    >>> from inelegant.fs import change_dir as cd
    >>> tempdir = os.path.dirname(docfile)
    >>> with cd(tempdir):
    ...     with tempfile(path='docfile', content='>>> 2+2\n4'):
    ...         suite = unittest.TestSuite()
    ...         add_doctest(suite, 'docfile')
    ...         suite.countTestCases()
    1

    This behavior is useful for quick tests (for example, from the console).
    Sometimes, however, we may want to specify the path to be used as
    reference. In these cases, we can use the ``working_dir`` argument. The
    doctest file will the be searched relative to the given working path::

    >>> path = os.path.join(tempdir, 'docfile')
    >>> with tempfile(path=path, content='>>> 2+2\n4'):
    ...     suite = unittest.TestSuite()
    ...     add_doctest(suite, 'docfile', working_dir=tempdir)
    ...     suite.countTestCases()
    1

    This is specially useful to give the path of the current module to be used.
    This way, we can ship documentation with the code itself.
    """
    if working_dir is None:
        working_dir = os.getcwd()

    if inspect.ismodule(doctestable):
        finder = doctest.DocTestFinder(exclude_empty=exclude_empty)
        doctest_suite = doctest.DocTestSuite(doctestable, test_finder=finder)
    else:
        if os.path.isabs(doctestable):
            path = doctestable
        else:
            path = os.path.join(working_dir, doctestable)

        doctest_suite = doctest.DocFileSuite(path, module_relative=False)

    suite.addTest(doctest_suite)


def add_module(suite, module, skip=None):
    """
    Add all test cases and test suites from the given module into the given
    suite.

    Consider the test cases below...

    ::

    >>> class TestCase1(unittest.TestCase):
    ...     def test1(self):
    ...         self.assertEquals(1, 1)
    >>> class TestCase2(unittest.TestCase):
    ...     def testFail(self):
    ...         self.assertEquals(1, 0)

    If they are in a module, and we call ``add_module()`` with this module and
    a suite, the tests will be found in the suite::

    >>> from inelegant.module import installed_module
    >>> with installed_module('t', defs=[TestCase1, TestCase2]) as t:
    ...     suite = unittest.TestSuite()
    ...     add_module(suite, t)
    ...     suite.countTestCases()
    2

    The function also accepts an argument, ``skip``. It should be either a test
    case class or an iterator yielding test case classes. If any of the classes
    is found in the module, it will not be added to the suite::

    >>> from inelegant.module import installed_module
    >>> with installed_module('t', defs=[TestCase1, TestCase2]) as t:
    ...     suite = unittest.TestSuite()
    ...     add_module(suite, t, skip=TestCase2)
    ...     suite.countTestCases()
    1
    """
    skip = to_set(skip)

    loaded_suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    test_cases = flatten(loaded_suite)

    suite.addTests(
        tc for tc in test_cases if tc.__class__ not in skip
    )


def to_set(value):
    """
    Converts a specific value to a set in the following ways:

    * If the value is ``None``, then returns the empty set::

        >>> to_set(None)
        set([])

    * If the value is an iterable, creates a set with all values from it::

        >>> to_set(xrange(3)) == set([0, 1, 2])
        True

    (Pay attention to never pass a huge or infinite iterator to ``to_set()``.)

    * Otherwise, returns a tuple containing the given value::

        >>> to_set(3)
        set([3])
    """
    if value is None:
        result = set()
    else:
        try:
            result = set(value)
        except TypeError:
            result = set([value])

    return result


def flatten(value, ids=None, depth=None):
    """
    Flattens an iterator::

        >>> a = [1, [[2, 3, (4, 5, xrange(6, 10)), 10], (11, 12)], [13], 14]
        >>> list(flatten(a))
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

    It prevents infinite loops with recursive iterators::

        >>> b = [1, 2, 3]
        >>> c = [4, 5, 6, b, 7]
        >>> b.append(c)
        >>> list(flatten(b))
        [1, 2, 3, 4, 5, 6, 7]
    """
    if ids is None:
        ids = set()

    try:
        for v in value:
            if id(v) in ids:
                continue
            ids.add(id(v))

            for u in flatten(v, ids=ids):
                yield u
    except TypeError:
        yield value
