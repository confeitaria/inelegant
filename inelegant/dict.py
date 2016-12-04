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
def temp_key(d, key, value):
    """
    ``temp_key()`` is a context manager that adds a key and a value to a dict
    during its context. Something like this::

    >>> d = {}
    >>> with temp_key(d, key='a', value=1):
    ...     d
    {'a': 1}

    Once the context finishes, the key is gone::

    >>> d
    {}

    The context manager yields the dict itself::
    >>> d = {}
    >>> with temp_key(d, key='a', value=1) as d1:
    ...     d is d1
    True
    """
    key_existed, previous_value = False, None

    if key in d:
        key_existed, previous_value = True, d[key]

    d[key] = value

    try:
        yield d
    finally:
        if key_existed:
            d[key] = previous_value
        else:
            del d[key]
