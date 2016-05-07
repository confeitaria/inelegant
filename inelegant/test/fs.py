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
import os

from inelegant.fs import cd

from inelegant.finder import TestFinder


class TestCd(unittest.TestCase):

    def test_cd_goes_to_dir_and_returns(self):
        """
        During the context of ``inelegant.fs.cd()``, it should go to another
        directory and then return to the current one.
        """
        prevdir = os.getcwd()
        tempdir = tempfile.mkdtemp()

        with cd(tempdir) as p:
            self.assertEquals(tempdir, os.getcwd())
            self.assertNotEquals(prevdir, tempdir)

            self.assertEquals(p, tempdir)

        self.assertEquals(prevdir, os.getcwd())

        os.rmdir(tempdir)

load_tests = TestFinder(__name__, 'inelegant.fs').load_tests

if __name__ == "__main__":
    unittest.main()
