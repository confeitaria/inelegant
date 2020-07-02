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

def temp_attr(object, field_name, value):
    return TemporaryAttributeReplacer(object, field_name, value)

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
        self.existed = None
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

