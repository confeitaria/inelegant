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

from inelegant.toggle import Toggle

from inelegant.finder import TestFinder


class TestToggle(unittest.TestCase):

    def test_toggle_is_disabled(self):
        """
        Toggles are disabled by default..
        """
        toggle = Toggle()

        self.assertFalse(toggle.enabled)

    def test_enable_toggle(self):
        """
        When the ``enable()`` method is called, the ``enabled`` attribute
        should be ``True``.
        """
        toggle = Toggle()

        self.assertFalse(toggle.enabled)

        toggle.enable()

        self.assertTrue(toggle.enabled)

    def test_disable_toggle(self):
        """
        When the ``disable()`` method is called, the ``enabled`` attribute
        should be ``False``.
        """
        toggle = Toggle()

        self.assertFalse(toggle.enabled)

        toggle.enable()

        self.assertTrue(toggle.enabled)

        toggle.disable()

        self.assertFalse(toggle.enabled)

    def test_toggle_as_context_manager(self):
        """
        A toggle can be used as a context manager. In this case, it will be
        enabled during the context but disabled after it.
        """
        toggle = Toggle()

        self.assertFalse(toggle.enabled)

        with toggle:
            self.assertTrue(toggle.enabled)

        self.assertFalse(toggle.enabled)

    def test_toggle_disabled_after_exception_in_context(self):
        """
        If an exception is raised during the toggle's context, the toggle
        should be disabled nonetheless.
        """
        toggle = Toggle()

        self.assertFalse(toggle.enabled)

        try:
            with toggle:
                raise Exception()
        except:
            pass

        self.assertFalse(toggle.enabled)

    def test_toggle_preserves_status_after_context(self):
        """
        If a toggle was enabled before managing a context, it should still be
        enabled after managing it.
        """
        toggle = Toggle()

        toggle.enable()

        with toggle:
            self.assertTrue(toggle.enabled)

        self.assertTrue(toggle.enabled)


load_tests = TestFinder(__name__, 'inelegant.toggle').load_tests

if __name__ == "__main__":
    unittest.main()
