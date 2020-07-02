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

from inelegant.object import temp_attr

from inelegant.finder import TestFinder


class TestTemporaryAttributeReplace(unittest.TestCase):

    def test_as_context_manager(self):
        """
        ``inelegant.object.AttributeReplacer`` is a context manager that
        temporarily sets or replaces the value of an attribute of an object.
        """
        class C:
            def __init__(self, field):
                self.field = field
        c = C(3)
        with temp_attr(c, 'field', 4):
            self.assertEqual(c.field, 4)
        self.assertEqual(c.field, 3)

    def test_as_context_manager_removes_previously_non_existent_attr(self):
        """
        ``inelegant.object.AttributeReplacer`` is a context manager that
        temporarily sets or replaces the value of an attribute of an object.
        If the attribute didn't exist before, it shouldn't exist after.
        """
        class C:
            pass
        c = C()
        with temp_attr(c, 'other_field', 4):
            self.assertEqual(c.other_field, 4)
        with self.assertRaises(AttributeError):
            c.other_field


load_tests = TestFinder(__name__, 'inelegant.object').load_tests

if __name__ == "__main__":
    unittest.main()
