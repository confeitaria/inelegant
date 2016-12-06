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


@contextlib.contextmanager
def redirect_stdout(output=None):
    if output is None:
        output = StringIO()

    temp, sys.stdout = sys.stdout, output

    try:
        yield output
    finally:
        sys.stdout = temp


@contextlib.contextmanager
def redirect_stderr(output=None):
    if output is None:
        output = StringIO()

    temp, sys.stderr = sys.stderr, output

    try:
        yield output
    finally:
        sys.stderr = temp
