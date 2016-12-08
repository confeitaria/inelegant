#!/usr/bin/env python
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

from __future__ import print_function

import unittest

import sys

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from inelegant.io import redirect_stdout, redirect_stderr

from inelegant.finder import TestFinder


class TestRedirectStdout(unittest.TestCase):

    def test_redirect_stdout(self):
        """
        ``inelegant.io.redirect_stdout()`` is a context manager that redirects
        the output of stdout to a file-like object.
        """
        output = StringIO()

        with redirect_stdout(output):
            print('test')

        print('non-redirected')

        self.assertEquals('test\n', output.getvalue())

    def test_redirect_stdout_yields_output(self):
        """
        If no argument is given to ``inelegant.io.redirect_stdout()``, it will
        yield a ``StringIO`` object.
        """
        with redirect_stdout() as output:
            print('test')

        self.assertEquals('test\n', output.getvalue())

    def test_do_not_redirect_stdout_after_exception_in_context(self):
        """
        ``inelegant.io.redirect_stdout()`` should restore stdout after the
        context even if an exception was raised.
        """
        output = StringIO()

        try:
            with redirect_stdout(output):
                raise Exception()
        except:
            pass

        print('non-redirected')

        self.assertEquals('', output.getvalue())

    def test_redirect_stdout_as_decorator(self):
        """
        ``inelegant.io.redirect_stdout()`` should also behave as a decorator.
        """
        output = StringIO()

        @redirect_stdout(output)
        def f():
            print('test')

        f()

        self.assertEquals('test\n', output.getvalue())

    def test_redirect_stdout_without_arg_as_decorator(self):
        """
        ``inelegant.io.redirect_stdout()`` should also behave as a decorator
        even if it is not given an argument. In this case, the output will be
        discarded.
        """
        @redirect_stdout
        def f():
            print('test')

        with redirect_stdout() as output:
            print('caught')
            f()

        self.assertEquals('caught\n', output.getvalue())

    def test_redirect_stdout_is_well_behaved_decorator(self):
        """
        ``inelegant.io.redirect_stdout()``, when acting as a decorator, should
        return a function that receives all arguments the decorated function
        would expect, and the function should return the expected value.
        """
        output = StringIO()

        @redirect_stdout(output)
        def f(a, b):
            return 3

        value = f('te', b='st')

        self.assertEquals(3, value)

    def test_redirect_stdout_without_arg_is_well_behaved_decorator(self):
        """
        ``inelegant.io.redirect_stdout()``, when acting as a decorator, should
        return a function that receives all arguments the decorated function
        would expect, and the function should return the expected value.
        """
        @redirect_stdout
        def f(a, b):
            return 3

        value = f('te', b='st')

        self.assertEquals(3, value)


class TestRedirectStderr(unittest.TestCase):

    def test_redirect_stderr(self):
        """
        ``inelegant.io.redirect_stderr()`` is a context manager that redirects
        the output of stderr to a file-like object.
        """
        output = StringIO()

        with redirect_stderr(output):
            print("test", file=sys.stderr)

        print('non-redirected', file=sys.stderr)

        self.assertEquals('test\n', output.getvalue())

    def test_do_not_redirect_stderr_after_exception_in_context(self):
        """
        ``inelegant.io.redirect_stderr()`` should restore stdout after the
        context even if an exception was raised.
        """
        output = StringIO()

        try:
            with redirect_stderr(output):
                raise Exception()
        except:
            pass

        print('non-redirected', file=sys.stderr)

        self.assertEquals('', output.getvalue())

    def test_redirect_stderr_yields_output(self):
        """
        If no argument is given to ``inelegant.io.redirect_stderr()``, it will
        yield a ``StringIO`` object.
        """
        with redirect_stderr() as output:
            print('test', file=sys.stderr)

        self.assertEquals('test\n', output.getvalue())

    def test_do_not_redirect_stderr_after_exception_in_context(self):
        """
        ``inelegant.io.redirect_stdout()`` should restore stdout after the
        context even if an exception was raised.
        """
        output = StringIO()

        try:
            with redirect_stdout(output):
                raise Exception()
        except:
            pass

        print('test', file=sys.stderr)

        self.assertEquals('', output.getvalue())


load_tests = TestFinder(__name__, 'inelegant.io').load_tests

if __name__ == "__main__":
    unittest.main()
