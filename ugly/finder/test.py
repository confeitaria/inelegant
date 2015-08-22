import unittest

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
