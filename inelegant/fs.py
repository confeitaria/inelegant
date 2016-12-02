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
import sys
import tempfile
import shutil
import contextlib
import errno


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
def temp_file(path=None, content=None, name=None, where=None, dir=None):
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
    specific directory, you can use the ``where`` argument::

    >>> with temp_dir() as tempdir:
    ...     with temp_file(where=tempdir) as p:
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
    if where is None:
        if dir is not None:
            sys.stderr.write('Do not use dir argument, use where.')
            where = dir

    where = decide_where(where)
    path = decide_path(path, name, where=where)

    if path is not None:
        if os.path.exists(path):
            raise IOError('File "{0}" already exists.'.format(path))

        f = open(path, 'w')
    else:
        f = tempfile.NamedTemporaryFile(dir=where, delete=False)
        path = f.name

    if content is not None:
        with f:
            f.write(content)

    try:
        yield path
    finally:
        os.remove(path)


@contextlib.contextmanager
def temp_dir(cd=False, path=None, where=None, name=None):
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

    Choosing the parent and the name
    =================================

    You can say where the temporary directory should be created with the
    ``where`` argument::

    >>> with temp_dir() as p1, temp_dir(where=p1) as p2:
    ...     os.path.isdir(p2)
    ...     os.path.dirname(p2) == p1
    True
    True

    It is also possible to choose the name of the directory::

    >>> with temp_dir(name='example') as p:
    ...     os.path.basename(p)
    'example'
    """
    where = decide_where(where)
    path = decide_path(path, name, where=where)

    if path is None:
        path = tempfile.mkdtemp(dir=where)
    else:
        os.makedirs(path)

    origin = os.getcwd()

    try:
        if cd:
            os.chdir(path)
        yield path
    finally:
        os.chdir(origin)
        shutil.rmtree(path)


@contextlib.contextmanager
def existing_dir(path=None, where=None, name=None, cd=False):
    """
    ``existing_dir()`` is a context manager that ensures a directory does
    exist. If it does exist, the function will yield a path to it::

    >>> with temp_dir() as p1:
    ...     with existing_dir(path=p1) as p2:
    ...         p1 == p2
    ...         os.path.exists(p2)
    True
    True

    If the directory does not exist, it will be created::

    >>> with temp_dir() as p1:
    ...     new_dir = os.path.join(p1, 'test')
    ...     with existing_dir(path=new_dir) as p2:
    ...         p2 == new_dir
    ...         os.path.isdir(p2)
    True
    True

    In the case the context did not previously exist, the directory will be
    removed::

    >>> with temp_dir() as p1:
    ...     new_dir = os.path.join(p1, 'test')
    ...     with existing_dir(path=new_dir) as p2:
    ...         os.path.exists(p2)
    ...     os.path.exists(p2)
    True
    False

    If the directory did exist previously, however, it will not be removed::

    >>> with temp_dir() as p1:
    ...     with existing_dir(path=p1) as p2:
    ...         os.path.exists(p2)
    ...     os.path.exists(p2)
    True
    True

    The arguments ``path``, ``where`` and ``name``
    ==============================================

    The contet manager can receive the path to the directory directly via its
    ``path`` argument. Sometimes, however, we have a path to a directory and
    the name of a directory we would create in this path. In this case, we can
    give these values to the context manager via the ``where`` and  ``name``
    arguments::

    >>> with temp_dir() as p1:
    ...     with existing_dir(where=p1, name='test') as p2:
    ...         p2 == os.path.join(p1, 'test')
    ...         os.path.exists(p2)
    ...     os.path.exists(p2)
    True
    True
    False
    """
    where = decide_where(where)
    path = decide_path(path, name, where)
    non_existent = missing_parent(path)

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            raise

    origin = os.getcwd()

    try:
        if cd:
            os.chdir(path)
        yield path
    finally:
        os.chdir(origin)

        if non_existent is not None:
            shutil.rmtree(non_existent)


def parent_paths(path):
    """
    Giving a path, returns a generator for all of its parents::

    >>> for sp in parent_paths('/usr/local/bin/sed'):
    ...     sp
    '/'
    '/usr'
    '/usr/local'
    '/usr/local/bin'
    '/usr/local/bin/sed'
    """
    components = path.split(os.sep)
    parent_path = root_path(path)

    for component in components:
        parent_path = os.path.join(parent_path, component)

        yield parent_path


def root_path(path, platform=None):
    """
    Returns a "file system root directory." In windows, the "root directory"
    is expected to bhe the drive of the current directory. In POSIX system, it
    is expected to be "/"::

    >>> root_path('/usr/local/bin/python', platform="posix")
    '/'

    On Windows, it would return the path's drive:

    >>> root_path(r'C:\\Program Files\\Python\\python.exe', platform="nt")
    'C:'

    (Currently, ``root_path()`` only support those two platforms, and does not
    support network paths, but it can be expanded to support any one that prove
    itself necessary.)

    The ``platform`` argument is optional. If it is not given, the function
    will ue the currenct platform's name::

    >>> root_path(os.path.curdir) == root_path(os.path.curdir,platform=os.name)
    True
    """
    if platform is None:
        platform = os.name

    if platform == "posix":
        root = "/"
    elif platform == "nt":
        root = path.split(':')[0] + ':'
    else:
        raise Excepton('root_path() does not work on "{0}"'.format(platform))

    return root


def missing_parent(path):
    """
    Given a path, return the first parent of it that does not exist::

    >>> with temp_dir(name='existing') as p:
    ...     missing = missing_parent(os.path.join(p, 'missing1', 'missing2'))
    ...     missing == os.path.join(p, 'missing1')
    True

    If all directories exist, return ``None``:

    >>> with temp_dir(name='existing') as p:
    ...     missing_parent(p) == None
    True
    """
    for parent in parent_paths(path):
        if not os.path.exists(parent):
            return parent

    return None


def decide_where(where):
    """
    Many functions in ``inelegant.fs`` receive an argument called ``where``.
    This argument should be a path to a directory _where_ the operations of the
    function are expected to be done. This argument is optional, so we have to
    provide a default value if it is not given.

    ``decide_where()`` decides whether to use the given value or the default
    one. If ``where`` is not ``None``, we have a value! Return it::

    >>> decide_where('/tmp')
    '/tmp'

    If ``where`` is ``None``, however, we have to use the default, that is
    given by ``tempfile.gettempdir()``::

    >>> decide_where(None) == tempfile.gettempdir()
    True
    """
    if where is None:
        where = tempfile.gettempdir()

    return where


def decide_path(path, name, where=None):
    """
    Many functions in ``inelegant.fs`` are supposed to create or operate on
    objects (files, directories) in the file system. Many times, these
    function can either receive a direct path to these objects, or can combine
    a directory where the object is and the name of this object.

    ``decide_path()`` decides which of those values are to be used. If ``path``
    is not ``None``, we have a value! Return it::

    >>> decide_path('/tmp/a', 'b', '/tmp')
    '/tmp/a'

    If ``path`` is ``None`` but ``name`` is not, the generated path will be an
    object with the given name in the ``where```directory::

    >>> decide_path(None, 'b', '/tmp')
    '/tmp/b'

    If ``where`` is ``None`` but a name is given, then the path will be an
    object with the given name at the system's default temporary directory::

    >>> decided_path = decide_path(None, 'b', None)
    >>> os.path.basename(decided_path)
    'b'
    >>> os.path.dirname(decided_path) == tempfile.gettempdir()
    True

    Finally, if a path is not given and a name is not given, then we cannot
    reliably generate a path for most purposes and the function returns
    ``None``::

    >>> decide_path(path=None, name=None, where='/tmp') == None
    True
    """
    where = decide_where(where)

    if path is None and name is not None:
        path = os.path.join(where, name)

    return path
