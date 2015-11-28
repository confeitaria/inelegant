#!/usr/bin/env python
#
# Copyright 2015, 2016 Adam Victor Brandizzi
#
# This file is part of Ugly.
#
# Ugly is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ugly is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Ugly.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import os, os.path

import ugly.finder.test
import ugly.module.test
import ugly.net.test
import ugly.process.test

from ugly.finder import TestFinder

readme_path = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    'readme.rst'
)

load_tests = TestFinder(
    readme_path,
    ugly.finder.test,
    ugly.module.test,
    ugly.net.test,
    ugly.process.test
).load_tests

if __name__ == "__main__":
    unittest.main()
