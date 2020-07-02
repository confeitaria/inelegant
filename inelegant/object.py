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

import contextlib


@contextlib.contextmanager
def temp_attr(object, attribute, value):
    """
    ``temp_attr`` replaces the attribute of an object temporarily.

    Context manager
    ===============

    As a context manager, it will replace the attribute during the context. For
    example, consider the object ``a`` below::

    >>> class A(object):
    ...     def __init__(self, b):
    ...         self.b = b
    >>> a = A(3)
    >>> a.b
    3

    We can use ``temp_attr`` to replace its value for a brief moment::

    >>> with temp_attr(a, attribute='b', value='ok'):
    ...     a.b
    'ok'

    Once the context is gone, the previous value is back::

    >>> a.b
    3

    Decorator
    =========

    ``temp_attr`` instances also behave as decorators. In this case, the value
    will be replaced during the function execution::

    >>> @temp_attr(a, attribute='b', value='ok')
    ... def f():
    ...     global a
    ...     print('The value of "a.b" is {0}.'.format(a.b))
    >>> a.b
    3
    >>> f()
    The value of "a.b" is ok.
    >>> a.b
    3

    What happens with non-existent attributes
    =========================================

    If there was no such attribute before, then it should not exist after::

    >>> with temp_attr(a, attribute='c', value='ok'):
    ...     a.c
    'ok'
    >>> a.c
    Traceback (most recent call last):
      ...
    AttributeError: 'A' object has no attribute 'c'

    Also, this is not supposed to work with objects which do not accept new
    attributes to be created:

    >>> with temp_attr(object(), attribute='c', value='fail'):
    ...     pass
    Traceback (most recent call last):
      ...
    AttributeError: 'object' object has no attribute 'c'
    """
    exists = hasattr(object, attribute)
    old_value = getattr(object, attribute, None)

    try:
        setattr(object, attribute, value)
        yield value
    finally:
        if exists:
            setattr(object, attribute, old_value)
        else:
            delattr(object, attribute)
