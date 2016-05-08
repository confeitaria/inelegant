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

from inelegant.fs import change_dir as cd, temporary_file

from inelegant.finder import TestFinder


class TestChangeDir(unittest.TestCase):

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

    def test_cd_returns_even_after_error(self):
        """
        If something happens during the execution of the context, it should
        not affect the returning to the original directory.
        """
        prevdir = os.getcwd()
        tempdir = tempfile.mkdtemp()

        with self.assertRaises(Exception):
            with cd(tempdir) as p:
                raise Exception()

        self.assertEquals(prevdir, os.getcwd())


class TestTemporaryFile(unittest.TestCase):

    def test_tempfile_create_file_yield_path_and_remove(self):
        """
        The ``inelegant.fs.temporary_file()`` context manager creates a
        temporary file, yields its path and, once the context is gone, removes
        the file.
        """
        with temporary_file() as p:
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isfile(p))

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_accepts_path(self):
        """
        ``inelegant.fs.temporary_file()`` accepts a path to a file.
        """
        path = os.path.join(tempfile.gettempdir(), 'myfile')

        with temporary_file(path) as p:
            self.assertEquals(path, p)
            self.assertTrue(os.path.exists(path))
            self.assertTrue(os.path.isfile(path))

        self.assertFalse(os.path.exists(path))
        self.assertFalse(os.path.isfile(path))

    def test_tempfile_accepts_dir(self):
        """
        ``inelegant.fs.temporary_file()`` can use an arbitrary directory given
        by the user.
        """
        with temporary_file(dir=tempfile.gettempdir()) as p:
            self.assertEquals(tempfile.gettempdir(), os.path.dirname(p))
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isfile(p))

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_accepts_content(self):
        """
        ``inelegant.fs.temporary_file()`` has an argument, ``content``, which
        can be a string. This string will be written to the file.
        """
        path = os.path.join(tempfile.gettempdir(), 'myfile')

        with temporary_file(content='Test') as p:
            with open(p) as f:
                self.assertEquals('Test', f.read())

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_fails_if_exists(self):
        """
        ``inelegant.fs.temporary_file()`` should fail if given a path to an
        existing file
        """
        path = os.path.join(tempfile.gettempdir(), 'myfile')

        with temporary_file() as p:
            with self.assertRaises(IOError):
                with temporary_file(p):
                    pass
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isfile(p))

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))


load_tests = TestFinder(__name__, 'inelegant.fs').load_tests

if __name__ == "__main__":
    unittest.main()
