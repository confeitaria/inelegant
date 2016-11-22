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


class Toggle(object):

    def __init__(self):
        self.enabled = False
        self._previous = None

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def __enter__(self):
        self._previous = self.enabled
        self.enable()

    def __exit__(self, *args):
        if not self._previous:
            self.disable()
