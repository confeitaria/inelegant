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

import os
import tempfile
import shutil
import contextlib


@contextlib.contextmanager
def change_dir(path):
    """
    ``inelegant.fs.change_dir()`` is a context manager to change directories.

    In tests, it is somewhat common to have to change directories. It may be a
    cumbersome process, though, because in general one has to go back to the
    previous directory even code fails. With ``change_dir()``, it becomes
    trivial::

    >>> curdir = os.getcwd()
    >>> with temp_dir() as tempdir:
    ...     with change_dir(tempdir):
    ...         os.getcwd() == curdir
    ...         os.getcwd() == tempdir
    False
    True
    >>> os.getcwd() == curdir
    True

    It yields the path to which it moved (which is very practical if one wants
    to give an expression to ``change_dir()``::

    >>> with temp_dir() as tempdir:
    ...     with change_dir(tempdir) as path:
    ...         os.getcwd() == path
    True
    """
    curdir = os.getcwd()
    os.chdir(path)

    try:
        yield path
    finally:
        os.chdir(curdir)


@contextlib.contextmanager
def temp_file(path=None, content=None, name=None, dir=None):
    """
    ``inelegant.fs.temp_file()`` is a context manager to operate on temporary
    files.

    Introduction
    ============

    In tests it is quite common to have to create a temporary file. However,
    the process for doing so is not very straightfoward because one should
    ensure the file is removed even if operations on it fail.

    With ``temp_file()``, we can do it very easily. We open a context and use
    it as its manager. The yielded value will be the path to the temporary
    file::

    >>> with temp_file() as p:
    ...     with open(p, 'w') as f:
    ...         f.write('test')
    ...     with open(p, 'r') as f:
    ...         f.read()
    'test'

    Once the context is finished, the file is removed::

    >>> open(p, 'r')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    IOError: ...

    Giving a path
    =============

    One can also give the path to the file to be created, if needed::

    >>> with temp_dir() as tempdir:
    ...     with temp_file(path=os.path.join(tempdir, 'test')) as p:
    ...         os.path.basename(p)
    ...         os.path.dirname(p) == tempdir
    ...         os.path.exists(p)
    'test'
    True
    True

    Pay attention, however: trying to create an already existing file will
    result in error, regardless of the permissions of the file::

    >>> with temp_file() as p:
    ...     with temp_file(path=p):
    ...         pass  # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    IOError: File "..." already exists.

    Choosing directory and name
    ===========================

    If you do not care about the file name but wants it to be created in a
    specific directory, you can use the ``dir`` argument::

    >>> with temp_dir() as tempdir:
    ...     with temp_file(dir=tempdir) as p:
    ...         os.path.dirname(p) == tempdir
    ...         os.path.exists(p)
    True
    True

    If you care about the name, but not the path, you can use the ``name``
    argument::

    >>> with temp_file(name='test') as p:
    ...     os.path.basename(p)
    'test'

    Inserting content
    =================

    Most of the time, we want to insert some content into the file, naturally.
    We do not need to open the file manually, however: the funtion has an
    argument, ``content``, that can receive the content of the file as a
    string::

    >>> with temp_file(content='example') as p:
    ...     with open(p, 'r') as f:
    ...         f.read()
    'example'
    """
    if dir is None:
        dir = tempfile.gettempdir()

    fid = None

    if path is None:
        if name is None:
            fid, path = tempfile.mkstemp(dir=dir)
        else:
            path = os.path.join(dir, name)

    if fid is None:
        if os.path.exists(path):
            raise IOError('File "{0}" already exists.'.format(path))
        open(path, 'a').close()

    if content is not None:
        with open(path, 'w') as f:
            f.write(content)

    try:
        yield path
    finally:
        os.remove(path)


@contextlib.contextmanager
def temp_dir(cd=False):
    """
    ``temp_dir()`` is a context manager to create temporary directories.

    Introduction
    ============

    In tests it is quite common to have to create a temporary directory.
    However, the process for doing so is not very straightfoward because one
    should ensure the directory is removed even if operations on it fail.

    With ``temp_dir()``, we can do it very easily. We open a context and use it
    as its manager. The yielded value will be the path to the temporary
    directory::

    >>> with temp_dir() as p:
    ...     os.path.isdir(p)
    True

    Once the context is done, the directory is gone::

    >>> os.path.isdir(p)
    False

    Changing the working directory
    ==============================

    In many cases, we want to change the current directory to the temporary
    one. In this case, we just need to make the ``cd`` argument true::

    >>> with temp_dir(cd=True) as p:
    ...     os.getcwd() == p
    True

    Again, once the context is closed, we are back to the previous directory::

    >>> curdir = os.getcwd()
    >>> with temp_dir(cd=True) as p:
    ...     os.getcwd() == curdir
    False
    >>> os.getcwd() == curdir
    True
    """
    origin = os.getcwd()
    path = tempfile.mkdtemp()

    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(origin)
        shutil.rmtree(path)
