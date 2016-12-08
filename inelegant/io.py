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


def redirect_stdout(arg=None):
    """
    ``redirect_stdout()`` replaces the current standward output for the
    file-like object given as an argument.

    As a context manager
    ====================

    ``redirect_stdout()`` can be used as a context manager::

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

    As a decorator
    ==============

    ``redirect_stdout()`` also behaves as a decorator. In this case, it will
    redirect any output during the function execution::

    >>> output = StringIO()
    >>> @redirect_stdout(output)
    ... def f(a, b):
    ...     print 'the args are', a, b
    ...     return a+b
    >>> f(1,2)
    3
    >>> output.getvalue()
    'the args are 1 2\\n'

    If you just want to suppress the output, you can use ``redirect_stdout()``
    directly, without giving an argument::

    >>> @redirect_stdout
    ... def g(a, b):
    ...     print 'the args are', a, b
    ...     return a*b
    >>> g(2,3)
    6
    """
    if callable(arg):
        decorator = RedirectContextManager(sys, 'stdout', StringIO())

        return decorator(arg)
    else:
        return RedirectContextManager(sys, 'stdout', arg)


def redirect_stderr(arg=None):
    """
    ``redirect_stderr()`` replaces the current standard error for the file-like
    object given as an argument

    As a context manager
    ====================

    ``redirect_stderr()`` can be used as a context manager::

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

    As a decorator
    ==============

    ``redirect_stderr()`` also behaves as a decorator. In this case, it will
    redirect any output during the function execution::

    >>> output = StringIO()
    >>> @redirect_stderr(output)
    ... def f(a, b):
    ...     sys.stderr.write('the args are {0} {1}\\n'.format(a, b))
    ...     return a+b
    >>> f(1,2)
    3
    >>> output.getvalue()
    'the args are 1 2\\n'

    If you just want to suppress the output, you can use ``redirect_stderr()``
    directly, without giving an argument::

    >>> @redirect_stderr
    ... def g(a, b):
    ...     sys.stderr.write('the args are {0} {1}\\n'.format(a, b))
    ...     return a*b
    >>> g(2,3)
    6
    """
    if callable(arg):
        decorator = RedirectContextManager(sys, 'stderr', StringIO())

        return decorator(arg)
    else:
        return RedirectContextManager(sys, 'stderr', arg)


class RedirectContextManager(object):

    def __init__(self, module, variable, output=None):
        if output is None:
            output = StringIO()

        self.module = module
        self.variable = variable
        self.output = output
        self.temp = None

    def __enter__(self):
        self.temp = getattr(self.module, self.variable)
        setattr(self.module, self.variable, self.output)

        return self.output

    def __exit__(self, type, value, traceback):
        setattr(self.module, self.variable, self.temp)

    def __call__(self, f):
        def decorator(f):

            def g(*args, **kwargs):
                with self:
                    return f(*args, **kwargs)

            return g

        return decorator(f)
