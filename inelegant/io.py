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

import contextlib
import sys

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class redirect_stdout(object):
    """
    ``redirect_stdout()`` replaces the current standward output for the
    file-like object given as an argument::

    >>> output = StringIO()
    >>> with redirect_stdout(output):
    ...     print 'ok'
    >>> output.getvalue()
    'ok\\n'

    Once the context is finished, the previous stdout is restored::

    >>> print 'back'
    back
    >>> output.getvalue()
    'ok\\n'

    The context yields the file-like object::

    >>> with redirect_stdout(StringIO()) as o:
    ...     print 'drop var'
    >>> o.getvalue()
    'drop var\\n'

    If no argument is given, it will create and yield a ``StringIO`` object to
    redirect the content to::

    >>> with redirect_stdout() as o:
    ...     print 'create it for me'
    >>> o.getvalue()
    'create it for me\\n'
    """

    def __init__(self, arg=None):
        function = None
        output = None

        if callable(arg):
            function = arg
        elif arg is not None:
            output = arg

        if output is None:
            output = StringIO()

        self.function = function
        self.output = output
        self.temp = None

    def __enter__(self):
        self.temp, sys.stdout = sys.stdout, self.output

        return self.output

    def __exit__(self, type, value, traceback):
        sys.stdout = self.temp

    def __call__(self, *args, **kwargs):
        if self.function is not None:
            with self:
                return self.function(*args, **kwargs)
        else:
            f = args[0]

            def g(*args, **kwargs):
                with self:
                    return f(*args, **kwargs)

            return g


class redirect_stderr(object):
    """
    ``redirect_stderr()`` replaces the current standard error for the file-like
    object given as an argument::

    >>> output = StringIO()
    >>> with redirect_stderr(output):
    ...     sys.stderr.write('ok\\n')
    >>> output.getvalue()
    'ok\\n'

    Once the context is finished, the previous stdout is restored::

    >>> sys.stderr.write('back\\n')
    >>> output.getvalue()
    'ok\\n'

    The context yields the file-like object::

    >>> with redirect_stderr(StringIO()) as o:
    ...     sys.stderr.write('drop var\\n')
    >>> o.getvalue()
    'drop var\\n'

    If no argument is given, it will create and yield a ``StringIO`` object to
    redirect the content to::

    >>> with redirect_stderr() as o:
    ...     sys.stderr.write('create it for me\\n')
    >>> o.getvalue()
    'create it for me\\n'
    """

    def __init__(self, arg=None):
        function = None
        output = None

        if callable(arg):
            function = arg
        elif arg is not None:
            output = arg

        if output is None:
            output = StringIO()

        self.function = function
        self.output = output
        self.temp = None

    def __enter__(self):
        self.temp, sys.stderr = sys.stderr, self.output

        return self.output

    def __exit__(self, type, value, traceback):
        sys.stderr = self.temp

    def __call__(self, *args, **kwargs):
        if self.function is not None:
            with self:
                return self.function(*args, **kwargs)
        else:
            f = args[0]

            def g(*args, **kwargs):
                with self:
                    return f(*args, **kwargs)

            return g
