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
    """
    Toggles are objects that represent a "on/off" status. Its main purpose is
    to enable deprecated behaviors.

    Enabling and disabling toggles
    ------------------------------

    A toggle is "turned off" by default::

    >>> toggle = Toggle()
    >>> toggle.enabled
    False

    It can be turned on with the ``enable()`` method::

    >>> toggle.enable()
    >>> toggle.enabled
    True

    To turn it off again, use the ``disable()`` method::

    >>> toggle.disable()
    >>> toggle.enabled
    False

    Toggles as context managers
    ---------------------------

    A remarkable advantage of toggles is that they can be used as context
    managers. In this case, they will be turned on during the context::

    >>> toggle.enabled
    False
    >>> with toggle:
    ...     toggle.enabled
    True

    If they were disabled before the context, they will be disabled after it::

    >>> toggle.enabled
    False

    Purpose and limitations
    -----------------------

    Toggles are a tool designed mainly to enable deprecated behaviors. They
    are expected to be enabled "once and for all:" at the beginning of the
    program, they are enabled and never again touched.

    The context manager's behavior is mostly thought for testing purposes.
    Using it for enabling more than one behavior in a program is unwise and
    dangerous: toggles are in no way thread-safe nd having two behaviors
    for the same function would be quite confusing.

    Ideally, if you turned on a toggle to enable a deprecated behavior, the
    best thing to do is to get rid of the use of the old behavior as soon as
    possible. They you can take advantage of the new one.
    """

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
