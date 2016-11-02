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

import unittest
import tempfile
import contextlib
import os
import os.path

from inelegant.module import installed_module, available_module
from inelegant.fs import temp_file as tempfile

from inelegant.finder import TestFinder


class TestTestFinder(unittest.TestCase):

    def test_is_test_suite(self):
        """
        The ``TestFinder`` class should be a test suite.
        """
        finder = TestFinder()

        self.assertTrue(isinstance(finder, unittest.TestSuite))

    def test_find_test_case_classes(self):
        """
        The ``TestFinder`` test suite should find test cases classes from the
        given modules.
        """

        class TestCase1(unittest.TestCase):

            def test_pass(self):
                pass

            def test_fail(self):
                self.fail()

        class TestCase2(unittest.TestCase):

            def test_pass(self):
                pass

            def test_error(self):
                raise Exception()

        with installed_module('m1', to_adopt=[TestCase1]) as m1, \
                installed_module('m2', to_adopt=[TestCase2]) as m2:
            result = unittest.TestResult()
            finder = TestFinder(m1, m2)
            finder.run(result)

            self.assertEquals(4, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(1, len(result.errors))

    def test_load_doctests(self):
        """
        The ``TestFinder`` test suite load the doctests found at the given
        modules.
        """

        class Class(object):
            """
            >>> 2+2
            4
            """

            def method(self):
                """
                >>> 3+3
                FAIL
                """
                pass

        def f(self):
            """
            >>> raise Exception()
            """
            pass

        with installed_module('m', to_adopt=[Class, f]) as m:
            result = unittest.TestResult()
            finder = TestFinder(m)
            finder.run(result)

            self.assertEquals(3, result.testsRun)
            self.assertEquals(2, len(result.failures))
            self.assertEquals(0, len(result.errors))

    def test_implement_load_tests(self):
        """
        One can delegate the ```load_tests()`` protocol`__ to the
        ``TestFinder`` by setting ``load_tests`` to the bound
        ``TestFinder.load_tests()`` at the module.

        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """

        class TestCase1(unittest.TestCase):

            def test_pass(self):
                pass

            def test_fail(self):
                self.fail()

        class TestCase2(unittest.TestCase):

            def test_pass(self):
                pass

            def test_error(self):
                raise Exception()

        with installed_module('m1', to_adopt=[TestCase1]) as m1, \
                installed_module('m2', to_adopt=[TestCase2]) as m2, \
                installed_module('m3') as m3:
            finder = TestFinder(m1, m2)

            m3.load_tests = finder.load_tests

            result = unittest.TestResult()
            suite = unittest.defaultTestLoader.loadTestsFromModule(m3)
            suite.run(result)

            self.assertEquals(4, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(1, len(result.errors))

    def test_accept_module_names(self):
        """
        If some of the arguments given to ``TestFinder`` are strings, then it
        will be assumed to be a module name. The module will be imported and
        then the seach will proceed on it.
        """

        class TestCase1(unittest.TestCase):

            def test_pass(self):
                pass

            def test_fail(self):
                self.fail()

            def test_error(self):
                raise Exception()

        class Class(object):
            """
            >>> 3+3
            6
            """

            def method(self):
                """
                >>> 2+2
                FAIL
                """
                pass

        with installed_module('m1', to_adopt=[TestCase1]), \
                installed_module('m2', to_adopt=[Class]):
            result = unittest.TestResult()
            finder = TestFinder('m1', 'm2')
            finder.run(result)

            self.assertEquals(5, result.testsRun)
            self.assertEquals(2, len(result.failures))
            self.assertEquals(1, len(result.errors))

    def test_does_not_accept_period_module(self):
        """
        The string ``'.'`` used to represent the current module, but we are not
        supporting it anymore.
        """
        with self.assertRaises(Exception):
            finder = TestFinder('.')

    def test_accept_file(self):
        """
        If a file object is given to ``TestFinder``, these files should be
        loaded as doctests.
        """
        content = """
        >>> 2+2
        4
        >>> 3+3
        'FAIL'
        """

        with tempfile(content=content) as path:
            with open(path, 'w') as f:
                f.write(content)

            with open(path) as f:
                result = unittest.TestResult()
                finder = TestFinder(f)
                finder.run(result)

                self.assertEquals(1, result.testsRun)
                self.assertEquals(1, len(result.failures))
                self.assertEquals(0, len(result.errors))

    def test_accept_file_path(self):
        """
        If a path to a file is given to ``TestFinder``, these files should be
        loaded as doctests.
        """
        content = """
        >>> 2+2
        4
        >>> 3+3
        'FAIL'
        """

        with tempfile(content=content) as path:
            with open(path, 'w') as f:
                f.write(content)

            result = unittest.TestResult()
            finder = TestFinder(path)
            finder.run(result)

            self.assertEquals(1, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(0, len(result.errors))

    def test_empty_file_no_error(self):
        """
        If the given file is empty, it should not result in error when trying
        to load the doctests.
        """
        with tempfile() as path:
            result = unittest.TestResult()
            finder = TestFinder(path)
            finder.run(result)

            self.assertEquals(1, result.testsRun)
            self.assertEquals(0, len(result.failures))
            self.assertEquals(0, len(result.errors))

    def test_file_relative_to_module(self):
        """
        If a relative path is given to ``TestFinder``, it should be accepted.
        The path should be relative to the module which created the test
        finder.
        """
        content = """
        >>> 2+2
        4
        >>> 3+3
        'FAIL'
        """
        path_dir = os.path.join(
            os.path.dirname(__file__),
            os.pardir
        )

        with tempfile(where=path_dir) as path:
            try:
                with open(path, 'w') as f:
                    f.write(content)
            except IOError:
                return unittest.skip('Cannot write on {0}'.format(path))

            name = os.path.basename(path)

            result = unittest.TestResult()
            finder = TestFinder(os.path.join(os.pardir, name))
            finder.run(result)

            self.assertEquals(1, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(0, len(result.errors))

    def test_get_test_loader(self):
        """
        ``get_test_loader()`` should find all tests from the arguments given to
        it and return a function compatible with the `load_tests() protocol`__.

        __ https://docs.python.org/2/library/unittest.html#load-tests-protocol
        """
        content = """
        >>> 2+2
        FAIL doctest file
        """

        with tempfile(content=content) as path:
            with open(path, 'w') as f:
                f.write(content)

            class Class:
                """
                >>> 3+3
                FAIL docstring
                """
                pass

            class TestCase1(unittest.TestCase):

                def test_fail1(self):
                    self.fail('TestCase1')

            class TestCase2(unittest.TestCase):

                def test_fail2(self):
                    self.fail('TestCase1')

            with installed_module('m', to_adopt=[Class]) as m, \
                    installed_module('t1', to_adopt=[TestCase1]) as t1, \
                    installed_module('t2', to_adopt=[TestCase2]) as t2:
                t2.load_tests = TestFinder(t1, m, path).load_tests

                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(t2)
                result = unittest.TestResult()
                suite.run(result)

                test_cases = {t[0] for t in result.failures}

                self.assertEquals(3, result.testsRun)
                self.assertEquals(3, len(result.failures))
                self.assertEquals(0, len(result.errors))

                method_names = {tc._testMethodName for tc in test_cases}

                self.assertIn('test_fail1', method_names)
                self.assertNotIn('test_fail2', method_names)

                class_names = {tc.__class__.__name__ for tc in test_cases}

                self.assertIn('TestCase1', class_names)
                self.assertIn('DocTestCase', class_names)
                self.assertIn('DocFileCase', class_names)
                self.assertNotIn('TestCase2', method_names)

    def test_skip_test_case(self):
        """
        The ``TestFinder`` test suite should be able to skip a test.
        """

        class TestCase1(unittest.TestCase):

            def test_pass(self):
                pass

            def test_fail(self):
                self.fail()

        class TestCase2(unittest.TestCase):

            def test_pass(self):
                pass

            def test_error(self):
                raise Exception()

        with installed_module('m1', to_adopt=[TestCase1]) as m1, \
                installed_module('m2', to_adopt=[TestCase2]) as m2:
            result = unittest.TestResult()
            finder = TestFinder(m1, m2, skip=TestCase2)
            finder.run(result)

            self.assertEquals(2, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(0, len(result.errors))

    def test_skip_test_cases(self):
        """
        The ``TestFinder`` test suite should be able to skip a list of tests.
        """

        class TestCase1(unittest.TestCase):

            def test_pass(self):
                pass

            def test_fail(self):
                self.fail()

        class TestCase2(unittest.TestCase):

            def test_pass(self):
                pass

            def test_error(self):
                raise Exception()

        with installed_module('m1', to_adopt=[TestCase1]) as m1, \
                installed_module('m2', to_adopt=[TestCase2]) as m2:
            result = unittest.TestResult()
            finder = TestFinder(m1, m2, skip=[TestCase2])
            finder.run(result)

            self.assertEquals(2, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(0, len(result.errors))

    def test_do_not_skip_subclass(self):
        """
        The ``TestFinder`` test suite should not skip subclasses from a skipped
        test case.
        """

        class BaseTestCase(unittest.TestCase):

            def test_fail(self):
                self.fail()

        class TestCase(BaseTestCase):

            def test_pass(self):
                pass

            def test_error(self):
                raise Exception()

        with installed_module('m1', to_adopt=[BaseTestCase]) as m1, \
                installed_module('m2', to_adopt=[TestCase]) as m2:
            result = unittest.TestResult()
            finder = TestFinder(m1, m2, skip=BaseTestCase)
            finder.run(result)

            self.assertEquals(3, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(1, len(result.errors))

    def test_fail_on_import_error_from_scanned_module(self):
        """
        If a scanned module raises ``ImportError``, it should fail the entire
        search.
        """
        with available_module('failed', code='raise ImportError()'):
            with self.assertRaises(ImportError):
                TestFinder('failed')

load_tests = TestFinder(__name__, 'inelegant.finder').load_tests

if __name__ == "__main__":
    unittest.main()
