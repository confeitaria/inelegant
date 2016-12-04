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

from inelegant.dict import temp_key

from inelegant.finder import TestFinder


class TestTempKey(unittest.TestCase):

    def test_yield_dict(self):
        """
        ``inelegant.dict.temp_key()`` should yield the dict it received.
        """
        original = {}

        with temp_key(original, key='a', value=1) as yielded:
            self.assertIs(original, yielded)

    def test_create_key(self):
        """
        ``inelegant.dict.temp_key()`` adds a key to a dict only during its
        context.
        """
        d = {}

        with temp_key(d, key='a', value=1):
            self.assertEquals({'a': 1}, d)

        self.assertEquals({}, d)

    def test_restore_key(self):
        """
        ``inelegant.dict.temp_key()`` restores a previous key value if it
        existed.
        """
        d = {'a': 'b'}

        with temp_key(d, key='a', value=1):
            self.assertEquals({'a': 1}, d)

        self.assertEquals({'a': 'b'}, d)

    def test_remove_key_after_exception_in_context(self):
        """
        ``inelegant.dict.temp_key()`` should remove the key even if an
        exception happened in the context.
        """
        d = {}

        try:
            with temp_key(d, key='a', value=1):
                self.assertEquals({'a': 1}, d)
                raise Exception()
        except:
            pass

        self.assertEquals({}, d)

    def test_restore_key_after_exception_in_context(self):
        """
        ``inelegant.dict.temp_key()`` should restore the key even if an
        exception happened in the context.
        """
        d = {'a': 'b'}

        try:
            with temp_key(d, key='a', value=1):
                self.assertEquals({'a': 1}, d)
                raise Exception()
        except:
            pass

        self.assertEquals({'a': 'b'}, d)


load_tests = TestFinder(__name__, 'inelegant.dict').load_tests

if __name__ == "__main__":
    unittest.main()
