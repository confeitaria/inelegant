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
import pkgutil
import sys

from inelegant.module import create_module, installed_module, \
    available_module, available_resource, adopt, AdoptException, \
    create_module_installs_module, available_resource_uses_path_as_where

from inelegant.io import redirect_stderr, suppress_stderr
from inelegant.finder import TestFinder


class TestCreateModule(unittest.TestCase):

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

    def test_create_module_does_not_install_module(self):
        """
        ``inelegant.module.create_module()`` should not add the created module
        to ``sys.modules`` so it cannot be imported.
        """
        m = create_module('example')

        with self.assertRaises(ImportError):
            import example

    def test_create_module_restore_previous_module(self):
        """
        If we create a module with a name already used by other module, the
        previous module should be available after the module creation.
        """
        with installed_module('m', code='x = 1'):
            m1 = create_module('m', code='x = 2')
            self.assertEquals(2, m1.x)

            import m
            self.assertEquals(1, m.x)

    @suppress_stderr
    def test_create_module_installs_module_with_toggle(self):
        """
        If your code relies in the old behavior of ``create_module()`` where it
        installs the module for importing, then you can enable this behavior
        back using the ``inelegant.module.create_module_installs_module``
        toggle.
        """
        with create_module_installs_module:
            m = create_module('example')
            import example
            self.assertEquals(m, example)

            del sys.modules['example']

    def test_create_module_installs_module_with_toggle_give_warning(self):
        """
        If your code relies in the old behavior of ``create_module()`` where it
        installs the module for importing, then you can enable this behavior
        back using the ``inelegant.module.create_module_installs_module``
        toggle. Yet, you should be warned this behavior is deprecated
        """
        with create_module_installs_module, redirect_stderr() as err:
            m = create_module('example')
            self.assertTrue(err.getvalue())

            del sys.modules['example']

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

    def test_create_module_adopts_entities(self):
        """
        All classes and functions from the definition list should be adopted by
        the module made by ``create_module()``.
        """

        class Class(object):

            def method(self):
                pass

        def function(a):
            pass

        m = create_module('example', to_adopt=(Class, function))

        self.assertEquals(m.__name__, Class.__module__)
        self.assertEquals(m.__name__, Class.method.__module__)
        self.assertEquals(m.__name__, function.__module__)

    @suppress_stderr
    def test_create_module_adopts_entities_with_defs_arguments(self):
        """
        ``create_module()`` should accept the deprected ``defs`` argument.
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

    def test_create_module_defs_argument_print_warning(self):
        """
        The use of the ``create_module()``'s ``defs`` argument should result in
        a warning.
        """
        def function(a):
            pass

        with redirect_stderr() as err:
            m = create_module('example', defs=(function,))

            self.assertTrue(err.getvalue())

    def test_create_module_set_def_entities_in_module(self):
        """
        The entities at the ``to_adopt`` list should be set into the module as
        their ``name`` values.
        """

        class Class(object):
            pass

        def function(a):
            pass

        with installed_module('example', to_adopt=(Class, function)) as m:
            self.assertEquals(m.Class, Class)
            self.assertEquals(m.function, function)

    @suppress_stderr
    def test_create_module_set_adoptee_entities_in_module_with_def(self):
        """
        The ``defs`` argument, although deprecated, should add entities to the
        module.
        """

        class Class(object):
            pass

        def function(a):
            pass

        with installed_module('example', defs=(Class, function)) as m:
            self.assertEquals(m.Class, Class)
            self.assertEquals(m.function, function)

    def test_create_module_defines_module_name_in_code(self):
        """
        The value of ``__name__`` for the executed code should be the name of
        the module.
        """
        m = create_module('m', code='value = __name__')

        self.assertEquals('m', m.value)

    def test_create_module_ignores_code_arg_indentation(self):
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

        m = create_module('m', code=code)

        self.assertEquals(3, m.three())
        self.assertEquals('a', m.a())

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


class TestInstalledModule(unittest.TestCase):

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

    def test_installed_module_uninstalls_module_after_exception(self):
        """
        When exiting the ``with`` block,
        ``inelegant.module.installed_module()`` uninstalls its module from
        ``sys.modules``, even and especially if an exception was raised during
        the context.
        """
        try:
            with installed_module('example') as m:
                raise Exception
        except:
            pass

        with self.assertRaises(ImportError):
            import example

    def test_installed_module_can_import_itself(self):
        """
        A module should be able to import itself if installed.
        """
        with installed_module('m', code='import m') as m:
            pass

    def test_to_adopt_are_already_adopted_on_code_execution(self):
        """
        The objects from the to-adopt list should be already adopted once the
        code is executed.
        """
        def f():
            pass

        with installed_module('m', to_adopt=[f], code='v = f.__module__') as m:
            self.assertEquals('m', m.v)

    def test_installed_module_restore_previous_module(self):
        """
        If we call ``installed_module()`` given an already existing module,
        the existing module should be restored.
        """
        with installed_module('m', code='x = 1'):

            with installed_module('m', code='x = 2'):
                import m
                self.assertEquals(2, m.x)

            import m
            self.assertEquals(1, m.x)


class TestAdopt(unittest.TestCase):

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
                installed_module('m2', to_adopt=[OuterClass]) as m2:
            adopt(m1, Class1)

            self.assertEquals(m1.__name__, Class1.__module__)
            self.assertEquals(m1.__name__, Class1.Class2.__module__)
            self.assertNotEquals(m1.__name__, Class1.UnadoptedClass.__module__)

    @suppress_stderr
    def test_adopts_internal_class_with_defs(self):
        """
        When ``inelegant.module.adopt()`` is called on a class, it adopts any
        other classes defined inside the adoptee, even if the class is given
        through the ``defs`` argument.
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


class TestAvailableModule(unittest.TestCase):

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

    def test_available_module_is_unavailable_after_context_exception(self):
        """
        ``inelegant.module.available_module()`` should vanish after its context
        ends, even and especially if an exception was raised from the context.
        """
        try:
            with available_module('example', code='x = 3') as p:
                raise Exception
        except:
            pass

        with self.assertRaises(ImportError):
            import example

    def test_available_module_does_not_raise_exception_from_code(self):
        """
        ``inelegant.module.available_module()`` does not import the module by
        default, which allows us to write modules that raise exceptions only
        when imported later.
        """
        with available_module('example', code='raise Exception()'):
            pass

            with self.assertRaises(Exception):
                import example


class TestAvailableResource(unittest.TestCase):

    def test_available_resource(self):
        """
        We should be able to add resources to an available module.
        """
        with available_module('example'):
            with available_resource('example', 'test.txt', content='test'):
                content = pkgutil.get_data('example', 'test.txt')
                self.assertEquals('test', content)

    def test_availabe_resource_in_subdir(self):
        """
        We should be able add resources to subdirectories of an available
        module.
        """
        with available_module('example'):
            with available_resource('example', 'a/b/test.txt', content='test'):
                content = pkgutil.get_data('example', 'a/b/test.txt')
                self.assertEquals('test', content)

    @suppress_stderr
    def test_availabe_resource_uses_path_as_where_with_toggle(self):
        """
        We can use the ``path`` argument as a prefix to the ``name`` argument
        if we enable the available_resource_uses_path_as_where toggle.
        """
        with available_resource_uses_path_as_where:
            with available_module('example'):
                with available_resource(
                        'example', 'test.txt', path='a/b', content='test'):
                    content = pkgutil.get_data('example', 'a/b/test.txt')
                    self.assertEquals('test', content)

    def test_availabe_resource_path_as_where_prints_warning(self):
        """
        The user should be warned about using ``path`` argument as a prefix to
        the ``name`` argument.
        """
        with redirect_stderr() as err, available_resource_uses_path_as_where:
            with available_module('example'):
                with available_resource(
                        'example', 'test.txt', path='a/b', content='test'):
                    self.assertTrue(err.getvalue())

    def test_availabe_resource_work_without_path_with_toggle(self):
        """
        If ``available_resource_uses_path_as_where`` is enabled, we are not
        forced to use ``path``.
        """
        with available_resource_uses_path_as_where:
            with available_module('example'):
                with available_resource('example', 'test.txt', content='test'):
                    content = pkgutil.get_data('example', 'test.txt')
                    self.assertEquals('test', content)

    def test_availabe_resource_uses_path_to_entire_file(self):
        """
        If we give a path argument to ``available_resource()`` it should create
        the resource in this path
        """
        with available_module('example'):
            with available_resource(
                    'example', path='a/b/test.txt', content='test'):
                content = pkgutil.get_data('example', 'a/b/test.txt')
                self.assertEquals('test', content)

    def test_availabe_resource_accepts_where_plus_name(self):
        """
        ``available_resource()`` should accept both the arguments ``where`` and
        ``name``. If it recieves such arguments (and does not recieve ``path``)
        then the resourced should be named ``name`` and located at the
        ``where`` subdirectory.
        """
        with available_module('example'):
            with available_resource(
                    'example', 'test.txt', where='a/b/', content='test'):
                content = pkgutil.get_data('example', 'a/b/test.txt')
                self.assertEquals('test', content)


load_tests = TestFinder(__name__, 'inelegant.module').load_tests

if __name__ == "__main__":
    unittest.main()
