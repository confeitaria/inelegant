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
import contextlib


@contextlib.contextmanager
def cd(path):
    """
    ``inelegant.fs.cd()`` is a context manager to change directories.

    In tests, it is somewhat common to have to change directories. It may be a
    cumbersome process, though, because in general one has to go back to the
    previous directory even code fails. With cd, it becomes trivial::

    >>> import tempfile
    >>> tempdir = tempfile.mkdtemp()
    >>> curdir = os.getcwd()
    >>> with cd(tempdir):
    ...     os.getcwd() == curdir
    ...     os.getcwd() == tempdir
    False
    True
    >>> os.getcwd() == curdir
    True

    >>> os.rmdir(tempdir)

    It yields the path to which it moved (which is very practical if one wants
    to give an expression to ``cd()``::

    >>> with cd(tempfile.mkdtemp()) as path:
    ...     os.getcwd() == path
    True

    >>> os.rmdir(path)
    """
    curdir = os.getcwd()
    os.chdir(path)

    yield path

    os.chdir(curdir)


@contextlib.contextmanager
def temporary_file(path=None, content=None):
    """
    ``inelegant.fs.temporary_file()`` is a context manager to operate on
    temporary files.

    Introduction
    ============

    In tests it is quite common to have to create a temporary file. However,
    the process for doing so is not very straightfoward because one should
    ensure the file is removed even if operations on it fail.

    With ``temporary_file()``, we can do it very easily. We open a context
    and use it as its manager. The yielded value will be the path to the
    temporary file.

    >>> with temporary_file() as p:
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

    >>> tempdir = tempfile.gettempdir()
    >>> with temporary_file(path=os.path.join(tempdir, 'test')) as p:
    ...     os.path.basename(p)
    ...     os.path.dirname(p) == tempdir
    ...     os.path.exists(p)
    'test'
    True
    True

    Pay attention, however: trying to create an already existing file will
    result in error, regardless of the permissions of the file::

    >>> with cd(tempdir):
    ...     with temporary_file(path='test') as p:
    ...         with temporary_file(path='test'):
    ...             pass  # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    IOError: File "test" already exists.

    Inserting content
    =================

    Most of the time, we want to insert some content into the file, naturally.
    We do not need to open the file manually, however: the funtion has an
    argument, ``content``, that can receive the content of the file as a
    string::

    >>> with temporary_file(content='example') as p:
    ...     with open(p, 'r') as f:
    ...         f.read()
    'example'
    """
    if path is None:
        _, path = tempfile.mkstemp()
    else:
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
