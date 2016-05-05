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
import inspect

from inelegant.module import create_module, installed_module, \
    available_module, adopt, AdoptException

from inelegant.finder import TestFinder


class TestModule(unittest.TestCase):

    def test_create_module(self):
        """
        ``inelegant.module.create_module()`` should create a module.
        """
        m = create_module('example')

        self.assertTrue(inspect.ismodule(m))
        self.assertTrue('example', m.__name__)

    def test_create_module_scope(self):
        """
        If ``inelegant.module.create_module()`` receives a dict as its
        ``scope`` argument, then the values from the dict should be set into
        the module.
        """
        m = create_module('example', scope={'x': 3})

        self.assertEquals(3, m.x)

    def test_create_module_code(self):
        """
        If ``inelegant.module.create_module()`` receives its ``code`` argument,
        then whatever it creates should be set in the module scope.
        """
        m = create_module('example', code='x = 3')

        self.assertEquals(3, m.x)

    def test_create_module_scope_code(self):
        """
        ``inelegant.module.create_module()`` can receive both ``scope`` and
        ``code`` arguments, in which case ``code`` can use anything from the
        scope.
        """
        m = create_module('example', scope={'x': 3}, code='x += 1')

        self.assertEquals(4, m.x)

    def test_create_module_installs_module(self):
        """
        ``inelegant.module.create_module()`` adds the created module to
        ``sys.modules`` so it can be imported.
        """
        m = create_module('example', scope={'x': 3})

        import example
        self.assertEquals(3, example.x)

    def test_installed_module(self):
        """
        ``inelegant.module.installed_module()`` returns a context manager. One
        can give it to the ``with`` statement and its result will be a module.
        ``inelegant.module.installed_module()`` accepts the same arguments from
        ``create_module()``.
        """
        with installed_module('example', scope={'x': 3}, code='x += 1') as m:
            self.assertEquals(4, m.x)

    def test_installed_module_uninstalls_module(self):
        """
        When exiting the ``with`` block,
        ``inelegant.module.installed_module()`` uninstalls its module from
        ``sys.modules``.
        """
        with installed_module('example') as m:
            import example

        with self.assertRaises(ImportError):
            import example

    def test_adopt(self):
        """
        ``inelegant.module.adopt()`` receives two arguments: a module and a
        "declared entity" (either a class or a function). It sets the
        ``__module__`` attribute of the entity to the module name, if possible.
        If the class has its own declared methods the ``__module__`` attribute
        of them is also set.
        """

        class Class(object):
            def method(self):
                pass

        def function(a):
            pass

        with installed_module('example') as m:
            adopt(m, Class)
            adopt(m, function)

            self.assertEquals(m.__name__, Class.__module__)
            self.assertEquals(m.__name__, Class.method.__module__)
            self.assertEquals(m.__name__, function.__module__)

    def test_create_module_does_not_adopt_scope_entities(self):
        """
        All classes and functions from the scope should not be adopted by the
        module made by ``create_module()``.
        """

        class Class(object):
            def method(self):
                pass

        def function(a):
            pass

        m = create_module(
            'example', scope={'Class': Class, 'function': function}
        )

        self.assertNotEquals(m.__name__, Class.__module__)
        self.assertNotEquals(m.__name__, Class.method.__module__)
        self.assertNotEquals(m.__name__, function.__module__)

    def test_create_module_adopts_def_entities(self):
        """
        All classes and functions from the definition list should be adopted by
        the module made by ``create_module()``.
        """

        class Class(object):

            def method(self):
                pass

        def function(a):
            pass

        m = create_module('example', defs=(Class, function))

        self.assertEquals(m.__name__, Class.__module__)
        self.assertEquals(m.__name__, Class.method.__module__)
        self.assertEquals(m.__name__, function.__module__)

    def test_create_module_set_def_entities_in_module(self):
        """
        The entities at the ``defs`` list should be set into the module as
        their ``name`` values.
        """

        class Class(object):
            pass

        def function(a):
            pass

        with installed_module('example', defs=(Class, function)) as m:
            self.assertEquals(m.Class, Class)
            self.assertEquals(m.function, function)

    def test_adopt_fails_on_read_only_module(self):
        """
        ``inelegant.module.adopt()`` raises an exception if required to adopt
        an object with read-only ``__module`` attr.
        """
        with installed_module('example') as m:
            with self.assertRaises(AdoptException):
                adopt(m, dict)

    def test_adopts_internal_class(self):
        """
        When ``inelegant.module.adopt()`` is called on a class, it adopts any
        other classes defined inside the adoptee.
        """
        class OuterClass(object):
            pass

        class Class1(object):
            class Class2(object):
                pass
            UnadoptedClass = OuterClass

        with installed_module('m1') as m1, \
                installed_module('m2', defs=[OuterClass]) as m2:
            adopt(m1, Class1)

            self.assertEquals(m1.__name__, Class1.__module__)
            self.assertEquals(m1.__name__, Class1.Class2.__module__)
            self.assertNotEquals(m1.__name__, Class1.UnadoptedClass.__module__)

    def test_module_name(self):
        """
        The value of ``__name__`` for the executd code should be the name of
        the module.
        """
        with installed_module('m', code='value = __name__') as m:
            self.assertEquals('m', m.value)

    def test_import_itself(self):
        """
        A module should be able to import itself if installed.
        """
        with installed_module('m', code='import m') as m:
            pass

    def test_defs_are_already_adopted_on_code_execution(self):
        """
        The objects from the defs list should be already adopted once the code
        is executed.
        """
        def f():
            pass

        with installed_module('m', defs=[f], code='v = f.__module__') as m:
            self.assertEquals('m', m.v)

    def test_ignore_code_arg_indentation(self):
        """
        If the string given as the code arg has some indentation not compatible
        with Python's syntax, it should be ignored provided the indentation is
        the same in all non-empty lines. Tabs cannot be mixed with spaces.
        C'mon, just use the four spaces...
        """
        code = """
            def three():
                return 3

            def a():
                return 'a'
        """

        with installed_module('m', code=code) as m:
            self.assertEquals(3, m.three())
            self.assertEquals('a', m.a())

    def test_adopt_code_defs(self):
        """
        Classes and functions created from the ``code`` arg should be adopted.
        """
        code = """
            def function():
                pass

            class Class():
                pass
        """

        with installed_module('m', code=code) as m:
            self.assertEquals('m', m.function.__module__)
            self.assertEquals('m', m.Class.__module__)

    def test_available_module_is_unavailable_after_context(self):
        """
        ``inelegant.module.available_module()`` should vanish after its context
        ends. If an instance of this is still available from a previous import,
        its behavior is undefined.
        """
        with available_module('example', code='x = 3') as p:
            self.assertEquals(None, p)

            import example
            self.assertEquals(3, example.x)

        with self.assertRaises(ImportError):
            import example

    def test_available_module_does_not_raise_exception_from_code(self):
        """
        ``inelegant.module.available_module()`` does not import the module by
        default, which allows us to write modules that raise exceptions only
        when imported later.
        """
        with available_module('example', code='raise Exception()') as p:
            pass

            with self.assertRaises(Exception):
                import example

    def test_create_module_does_not_register_failed_module(self):
        """
        If the code of a module raises an exception, it is not available for
        importing. Consequently, it should not be in ``sys.modules`` or be
        importable.
        """
        with self.assertRaises(Exception):
            create_module('m', code='raise Exception()')

        with self.assertRaises(ImportError):
            import m

load_tests = TestFinder(__name__, 'inelegant.module').load_tests

if __name__ == "__main__":
    unittest.main()
