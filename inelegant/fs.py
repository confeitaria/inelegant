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
    if path is None:
        _, path = tempfile.mkstemp()
    else:
        if os.path.exists(path):
            raise IOError('File "{0}" already exists.'.format(path))
        open(path, 'a').close()

    if content is not None:
        with open(path, 'w') as f:
            f.write(content)

    yield path

    os.remove(path)
