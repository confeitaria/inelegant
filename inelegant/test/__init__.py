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

import unittest
import os
import os.path

import inelegant

from inelegant.finder import TestFinder

readme_path = os.path.join(
    os.path.abspath(os.path.dirname(inelegant.__file__)),
    os.pardir,
    'readme.rst'
)

load_tests = TestFinder(
    readme_path,
    'inelegant.test.dict',
    'inelegant.test.finder',
    'inelegant.test.fs',
    'inelegant.test.io',
    'inelegant.test.module',
    'inelegant.test.net',
    'inelegant.test.process',
    'inelegant.test.toggle'
).load_tests
