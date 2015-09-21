import unittest
import tempfile
import contextlib
import os

from ugly.module import installed_module

from ugly.finder import TestFinder

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

        with installed_module('m1', scope={'TestCase1': TestCase1}) as m1, \
                installed_module('m2', scope={'TestCase2': TestCase2}) as m2:
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

        with installed_module('m', scope={'Class': Class, 'f': f}) as m:
            result = unittest.TestResult()
            finder = TestFinder(m)
            finder.run(result)

            self.assertEquals(3, result.testsRun)
            self.assertEquals(2, len(result.failures))
            self.assertEquals(0, len(result.errors))

    def test_implement_load_tests(self):
        """
        One can delegate the ```load_tests()`` protocol`__ to the ``TestFinder``
        by setting ``load_tests`` to the bound ``TestFinder.load_tests()`` at
        the module.

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

        with installed_module('m1', scope={'TestCase1': TestCase1}) as m1, \
                installed_module('m2', scope={'TestCase2': TestCase2}) as m2, \
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

        with installed_module('m1', scope={'TestCase1': TestCase1}), \
                installed_module('m2', scope={'Class': Class}):
            result = unittest.TestResult()
            finder = TestFinder('m1', 'm2')
            finder.run(result)

            self.assertEquals(5, result.testsRun)
            self.assertEquals(2, len(result.failures))
            self.assertEquals(1, len(result.errors))

    def test_accept_period_module(self):
        """
        If the sting ``'.'`` is given to ``TestFinder``, it should look for
        tests inside the module it was created.
        """
        period_tests = list(iter(TestFinder('.')))
        name_tests = list(iter(TestFinder(__name__)))

        self.assertEquals(period_tests, name_tests)

    def test_accept_file(self):
        """
        If a file object is given to ``TestFinder``, these files should be
        loaded as doctests.
        """
        _, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            f.write(
                '>>> 2+2\n'
                '4\n'
                '>>> 3+3\n'
                'FAIL'
            )

        with open(path) as f:
            result = unittest.TestResult()
            finder = TestFinder(f)
            finder.run(result)

            self.assertEquals(1, result.testsRun)
            self.assertEquals(1, len(result.failures))
            self.assertEquals(0, len(result.errors))

        os.remove(path)

    def test_accept_file_path(self):
        """
        If a path to a file is given to ``TestFinder``, these files should be
        loaded as doctests.
        """
        _, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            f.write(
                '>>> 2+2\n'
                '4\n'
                '>>> 3+3\n'
                'FAIL'
            )

        result = unittest.TestResult()
        finder = TestFinder(path)
        finder.run(result)

        self.assertEquals(1, result.testsRun)
        self.assertEquals(1, len(result.failures))
        self.assertEquals(0, len(result.errors))

        os.remove(path)

    def test_empty_file_no_error(self):
        """
        If the given file is empty, it should not result in error when trying
        to load the doctests.
        """
        _, path = tempfile.mkstemp()

        result = unittest.TestResult()
        finder = TestFinder(path)
        finder.run(result)

        self.assertEquals(1, result.testsRun)
        self.assertEquals(0, len(result.failures))
        self.assertEquals(0, len(result.errors))

        os.remove(path)


load_tests = TestFinder('.', 'ugly.finder.finder').load_tests

if __name__ == "__main__":
    unittest.main()
