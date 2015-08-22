import ugly.finder.test
import ugly.module.test

from ugly.finder import TestFinder

load_tests = TestFinder(ugly.finder.test, ugly.module.test).load_tests
