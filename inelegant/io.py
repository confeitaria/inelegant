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
    """
    if arg is None:
        arg = StringIO()

    return TemporaryAttributeReplacer(sys, 'stdout', arg)


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
    """
    if arg is None:
        arg = StringIO()

    return TemporaryAttributeReplacer(sys, 'stderr', arg)


class TemporaryAttributeReplacer(object):
    """
    ``TemporaryAttributeReplacer`` replaces the attribute of an object
    temporarily.

    Context manager
    ===============

    As a context manager, it will replace the attribute during
    the context. For example, consider the object ``a`` below::

    >>> class A(object):
    ...     def __init__(self, b):
    ...         self.b = b
    >>> a = A(3)
    >>> a.b
    3

    We can use ``TemporaryAttributeReplacer`` to replace its value for a brief
    moment::

    >>> with TemporaryAttributeReplacer(a, attribute='b', value='ok'):
    ...     a.b
    'ok'

    Once the context is gone, the previous value is back::

    >>> a.b
    3

    Decorator
    =========

    ``TemporaryAttributeReplacer`` instances also behave as decorators. In
    this case, the value will be replaced during the function execution::

    >>> @TemporaryAttributeReplacer(a, attribute='b', value='ok')
    ... def f():
    ...     global a
    ...     print('The value of "a.b" is {0}.'.format(a.b))
    >>> a.b
    3
    >>> f()
    The value of "a.b" is ok.
    >>> a.b
    3
    """

    def __init__(self, obj, attribute, value):
        self.obj = obj
        self.attribute = attribute
        self.value = value
        self.temp = None

    def __enter__(self):
        self.temp = getattr(self.obj, self.attribute)
        setattr(self.obj, self.attribute, self.value)

        return self.value

    def __exit__(self, type, value, traceback):
        setattr(self.obj, self.attribute, self.temp)

    def __call__(self, f):
        def decorator(f):

            def g(*args, **kwargs):
                with self:
                    return f(*args, **kwargs)

            return g

        return decorator(f)


def suppress_stdout(f=None):
    """
    ``suppress_stdout()`` ensures that no content is written in the standard
    output. It is done by replacing the standard output with a file-like object
    that saves nothing.

    Any content written to standard output while ``suppress_stdout()`` is
    effective will be lost. If you need to access this content, use
    ``redirect_stdout()``.

    ``suppress_stdout()`` can be used either as a context manager or as a
    decorator.

    As a context manager
    ====================

    As a context manager, ``suppress_stdout()`` receives no argument. Anything
    written to stdandard output during its context will be discarded. Once the
    context is finished, the previous standard output is restored::

    >>> print('redirected')
    redirected
    >>> with suppress_stdout():
    ...     print('discarded')
    >>> print('redirected, too')
    redirected, too

    As a decorator
    ==============

    ``suppress_stdout()`` also behaves as a decorator. In this case, it will
    suppress any output during the function execution::

    >>> @suppress_stdout
    ... def f(a, b):
    ...     print 'the args are', a, b
    ...     return a+b
    >>> f(1,2)
    3
    """
    output = open(os.devnull, 'w')
    replacer = redirect_stdout(output)

    if f is not None:
        return replacer(f)
    else:
        return replacer


def suppress_stderr(f=None):
    """
    ``suppress_stderr()`` ensures that no content is written in the standard
    error. It is done by replacing the standard output with a file-like object
    that saves nothing.

    Any content written to standard output while ``suppress_stderr()`` is
    effective will be lost. If you need to access this content, use
    ``redirect_stderr()``.

    ``suppress_stderr()`` can be used either as a context manager or as a
    decorator.

    As a context manager
    ====================

    As a context manager, ``suppress_stderr()`` receives no argument. Anything
    written to stdandard output during its context will be discarded. Once the
    context is finished, the previous standard output is restored::

    >>> with redirect_stderr() as output:
    ...     sys.stderr.write('redirected\\n')
    ...     with suppress_stderr():
    ...         sys.stderr.write('discarded\\n')
    ...     sys.stderr.write('redirected, too\\n')
    >>> output.getvalue()
    'redirected\\nredirected, too\\n'

    As a decorator
    ==============

    ``suppress_stderr()`` also behaves as a decorator. In this case, it will
    suppress any output during the function execution::

    >>> @suppress_stderr
    ... def f(a, b):
    ...     sys.stderr.write('the args are {0} {1}'.format(a, b))
    ...     return a+b
    >>> with redirect_stderr() as output:
    ...     f(1,2)
    3
    >>> output.getvalue()
    ''
    """
    output = open(os.devnull, 'w')
    replacer = redirect_stderr(output)

    if f is not None:
        return replacer(f)
    else:
        return replacer
