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

from inelegant.fs import change_dir as cd, temp_file, temp_dir, existing_dir

from inelegant.io import redirect_stderr
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
        The ``inelegant.fs.temp_file()`` context manager creates a
        temporary file, yields its path and, once the context is gone, removes
        the file.
        """
        with temp_file() as p:
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isfile(p))

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_accepts_path(self):
        """
        ``inelegant.fs.temp_file()`` accepts a path to a file.
        """
        path = os.path.join(tempfile.gettempdir(), 'myfile')

        with temp_file(path) as p:
            self.assertEquals(path, p)
            self.assertTrue(os.path.exists(path))
            self.assertTrue(os.path.isfile(path))

        self.assertFalse(os.path.exists(path))
        self.assertFalse(os.path.isfile(path))

    def test_tempfile_accepts_name(self):
        """
        ``inelegant.fs.temp_file()`` can use an arbitrary name given by the
        user.
        """
        with temp_file(name='test') as p:
            self.assertEquals('test', os.path.basename(p))
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isfile(p))

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_accepts_where(self):
        """
        ``inelegant.fs.temp_file()`` can use an arbitrary directory given
        by the user.
        """
        with temp_file(where=tempfile.gettempdir()) as p:
            self.assertEquals(tempfile.gettempdir(), os.path.dirname(p))
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isfile(p))

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_accepts_dir(self):
        """
        ``inelegant.fs.temp_file()`` can use an arbitrary directory given
        by the user via the deprecated ``dir`` argument.
        """
        with redirect_stderr() as err:
            with temp_file(dir=tempfile.gettempdir()) as p:
                self.assertEquals(tempfile.gettempdir(), os.path.dirname(p))
                self.assertTrue(os.path.exists(p))
                self.assertTrue(os.path.isfile(p))

        self.assertTrue(err.getvalue())

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_accepts_name_and_dir(self):
        """
        ``inelegant.fs.temp_file()`` can use both ``name`` and ``dir``
        together.
        """
        with temp_dir() as tmpdir:
            with temp_file(name='test', where=tmpdir) as p:
                self.assertEquals(os.path.join(tmpdir, 'test'), p)
                self.assertTrue(os.path.exists(p))
                self.assertTrue(os.path.isfile(p))

            self.assertFalse(os.path.exists(p))
            self.assertFalse(os.path.isfile(p))

    def test_tempfile_accepts_content(self):
        """
        ``inelegant.fs.temp_file()`` has an argument, ``content``, which
        can be a string. This string will be written to the file.
        """
        path = os.path.join(tempfile.gettempdir(), 'myfile')

        with temp_file(content='Test') as p:
            with open(p) as f:
                self.assertEquals('Test', f.read())

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))

    def test_tempfile_fails_if_exists(self):
        """
        ``inelegant.fs.temp_file()`` should fail if given a path to an
        existing file
        """
        path = os.path.join(tempfile.gettempdir(), 'myfile')

        with temp_file() as p:
            with self.assertRaises(IOError):
                with temp_file(p):
                    pass
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isfile(p))

        self.assertFalse(os.path.exists(p))
        self.assertFalse(os.path.isfile(p))


class TestTemporaryDirectory(unittest.TestCase):

    def test_tempdir_create_dir_yield_path_and_remove(self):
        """
        The ``inelegant.fs.temp_dir()`` context manager creates a temporary
        directory, yields its path and, once the context is gone, deletes the
        directory.
        """
        with temp_dir() as p:
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isdir(p))

        self.assertFalse(os.path.exists(p))

    def test_tempdir_auto_cd(self):
        """
        ``inelegant.fs.temp_dir()`` will change the current directory to the
        new temporary one the argument ``cd`` is ``True``.
        """
        origin = os.getcwd()

        with temp_dir(cd=True) as p:
            self.assertNotEquals(origin, os.getcwd())
            self.assertEquals(p, os.getcwd())

        self.assertEquals(origin, os.getcwd())
        self.assertFalse(os.path.exists(p))

    def test_tempdir_no_auto_cd(self):
        """
        ``inelegant.fs.temp_dir()`` will not change the current directory to
        the new temporary one the argument ``cd`` is ``False`` or not given.
        """
        origin = os.getcwd()

        with temp_dir(cd=False) as p:
            self.assertEquals(origin, os.getcwd())
            self.assertNotEquals(origin, p)

        with temp_dir() as p:
            self.assertEquals(origin, os.getcwd())
            self.assertNotEquals(origin, p)

        self.assertEquals(origin, os.getcwd())

    def test_tempdir_accepts_directory(self):
        """
        ``inelegant.fs.temp_dir()`` can choose in which directory to create the
        new one.
        """
        with temp_dir() as p1:

            with temp_dir(where=p1) as p2:
                self.assertTrue(os.path.isdir(p2))
                self.assertEquals(p1, os.path.dirname(p2))

            self.assertFalse(os.path.exists(p2))
            self.assertTrue(os.path.exists(p1))

        self.assertFalse(os.path.exists(p1))

    def test_tempdir_accepts_name(self):
        """
        ``inelegant.fs.temp_dir()`` can choose which name to use in the new
        directory.
        """
        with temp_dir(name='example') as p:
            self.assertTrue(os.path.isdir(p))
            self.assertEquals('example', os.path.basename(p))

        self.assertFalse(os.path.exists(p))

    def test_tempdir_accepts_name_directory(self):
        """
        ``inelegant.fs.temp_dir()`` can choose both which name to use in the
        new directory and where to create it.
        """
        with temp_dir() as p1:

            with temp_dir(where=p1, name='example') as p2:
                self.assertTrue(os.path.isdir(p2))
                self.assertEquals(p1, os.path.dirname(p2))
                self.assertEquals('example', os.path.basename(p2))

            self.assertFalse(os.path.exists(p2))
            self.assertTrue(os.path.exists(p1))

        self.assertFalse(os.path.exists(p1))

    def test_tempdir_name_can_be_path(self):
        """
        ``inelegant.fs.temp_dir()`` can receive a path as a name, and will
        create all directories in it.
        """
        with temp_dir(name='a/b/c') as p:
            self.assertTrue(os.path.isdir(p))

            self.assertEquals('c', os.path.basename(p))

            parent_dir = os.path.dirname(p)
            self.assertEquals('b', os.path.basename(parent_dir))

            grandparent_dir = os.path.dirname(parent_dir)
            self.assertEquals('a', os.path.basename(grandparent_dir))

        self.assertFalse(os.path.exists(p))


class TestExistingDirectory(unittest.TestCase):

    def test_existing_dir_create_dir_if_it_does_not_exist(self):
        """
        The ``inelegant.fs.existing_dir()`` context manager creates a temporary
        directory, yields its path and, once the context is gone, deletes the
        directory if it does not exist.
        """
        with temp_dir() as where:
            p = os.path.join(where, 'example')
            self.assertFalse(os.path.exists(p))

            with existing_dir(path=p) as p1:
                self.assertEquals(p1, p)
                self.assertTrue(os.path.exists(p))
                self.assertTrue(os.path.isdir(p))

            self.assertFalse(os.path.exists(p))

    def test_existing_dir_yield_dir_if_it_exists(self):
        """
        The ``inelegant.fs.existing_dir()`` context manager will just yield the
        dir if it already exists.
        """
        with temp_dir() as p:
            self.assertTrue(os.path.exists(p))

            with existing_dir(path=p) as p1:
                self.assertEquals(p1, p)
                self.assertTrue(os.path.exists(p))
                self.assertTrue(os.path.isdir(p))

        self.assertFalse(os.path.exists(p))

    def test_existing_dir_does_not_delete_existing_dir(self):
        """
        The ``inelegant.fs.existing_dir()`` context manager will just yield the
        dir if it already exists. It will not be deleted.
        """
        with temp_dir() as p:
            self.assertTrue(os.path.exists(p))

            with existing_dir(path=p) as p1:
                self.assertEquals(p1, p)
                self.assertTrue(os.path.exists(p))
                self.assertTrue(os.path.isdir(p))

            self.assertTrue(os.path.exists(p))

    def test_existing_dir_auto_cd(self):
        """
        ``inelegant.fs.existing_dir()`` will change the current directory to
        the new temporary one the argument ``cd`` is ``True``.
        """
        origin = os.getcwd()

        with temp_dir() as where:
            with existing_dir(where=where, name='example', cd=True) as p:
                self.assertNotEquals(origin, os.getcwd())
                self.assertEquals(p, os.getcwd())

            self.assertEquals(origin, os.getcwd())
            self.assertFalse(os.path.exists(p))

    def test_existing_dir_no_auto_cd(self):
        """
        ``inelegant.fs.existing_dir()`` will not change the current directory
        to the new temporary one the argument ``cd`` is ``False`` or not given.
        """
        origin = os.getcwd()

        with temp_dir() as where:
            with existing_dir(where=where, name='example', cd=False) as p:
                self.assertEquals(origin, os.getcwd())
                self.assertNotEquals(origin, p)

        with temp_dir() as where:
            with existing_dir(where=where, name='example', ) as p:
                self.assertEquals(origin, os.getcwd())
                self.assertNotEquals(origin, p)

        self.assertEquals(origin, os.getcwd())

    def test_existing_dir_accepts_directory(self):
        """
        ``inelegant.fs.existing_dir()`` can choose in which directory to create
        the new one.
        """
        with temp_dir() as where:
            with existing_dir(where=where, name='example') as p:
                self.assertTrue(os.path.exists(p))
                self.assertTrue(os.path.isdir(p))

            self.assertFalse(os.path.exists(p))

    def test_existing_dir_creates_container_directories_from_name(self):
        """
        If the ``where`` argument contains both existing and non-exististent
        directories, ``inelegant.fs.existing_dir()`` will create the needed
        ones and leave the other ones as-is.
        """
        with temp_dir() as where:

            with temp_dir(where=where, name='a') as a:

                self.assertEquals(os.path.join(where, 'a'), a)

                with existing_dir(where=where, name='a/b/example') as p:
                    self.assertEquals(
                        os.path.join(where, 'a', 'b', 'example'), p)

                    self.assertTrue(os.path.exists(p))
                    self.assertTrue(os.path.isdir(p))

                b = os.path.join(where, 'a', 'b')

                self.assertFalse(os.path.exists(p))
                self.assertFalse(os.path.exists(b))
                self.assertTrue(os.path.exists(a))

    def test_existing_dir_name_can_be_path(self):
        """
        ``inelegant.fs.existing_dir()`` can receive a path as a name, and will
        create all directories in it. If the path had to be created, it will
        be removed.
        """
        with temp_dir() as where:
            with existing_dir(where=where, name='a/b/c/example') as p:
                result = os.path.join(where, 'a', 'b', 'c', 'example')

                self.assertEquals(result, p)
                self.assertTrue(os.path.exists(p))
                self.assertTrue(os.path.exists(os.path.join(where, 'a')))

            self.assertFalse(os.path.exists(p))
            self.assertFalse(os.path.exists(os.path.join(where, 'a')))

    def test_existing_dir_creates_container_directories_from_where(self):
        """
        If the ``where`` argument contains both existing and non-exististent
        directories, ``inelegant.fs.existing_dir()`` will create the needed
        ones and leave the other ones as-is.
        """
        with temp_dir() as where:

            with temp_dir(where=where, name='a') as a:

                self.assertEquals(os.path.join(where, 'a'), a)

                with existing_dir(where=a, name='b/example') as p:
                    self.assertEquals(
                        os.path.join(where, 'a', 'b', 'example'), p)

                    self.assertTrue(os.path.exists(p))
                    self.assertTrue(os.path.isdir(p))

                b = os.path.join(where, 'a', 'b')

                self.assertFalse(os.path.exists(p))
                self.assertFalse(os.path.exists(b))
                self.assertTrue(os.path.exists(a))


load_tests = TestFinder(__name__, 'inelegant.fs').load_tests

if __name__ == "__main__":
    unittest.main()
