import unittest
import inspect

from ugly.module import create_module, installed_module, adopt, AdoptException

class TestModule(unittest.TestCase):

    def test_create_module(self):
        """
        ``ugly.module.create_module()`` should create a module.
        """
        m = create_module('example')

        self.assertTrue(inspect.ismodule(m))
        self.assertTrue('example', m.__name__)

    def test_create_module_scope(self):
        """
        If ``ugly.module.create_module()`` receives a dict as its ``scope``
        argument, then the values from the dict should be set into the module.
        """
        m = create_module('example', scope={'x': 3})

        self.assertEquals(3, m.x)

    def test_create_module_code(self):
        """
        If ``ugly.module.create_module()`` receives its ``code`` argument,
        then whatever it creates should be set in the module scope.
        """
        m = create_module('example', code='x = 3')

        self.assertEquals(3, m.x)

    def test_create_module_scope_code(self):
        """
        ``ugly.module.create_module()`` can receive both ``scope`` and ``code``
        arguments, in which case ``code`` can use anything from the scope.
        """
        m = create_module('example', scope={'x': 3}, code='x += 1')

        self.assertEquals(4, m.x)

    def test_create_module_installs_module(self):
        """
        ``ugly.module.create_module()`` adds the created module to
        ``sys.modules`` so it can be imported.
        """
        m = create_module('example', scope={'x': 3})

        import example
        self.assertEquals(3, example.x)

    def test_installed_module(self):
        """
        ``ugly.module.installed_module()`` returns a context manager. One can
        give it to the ``with`` statement and its result will be a module.
        ``ugly.module.installed_module()`` accepts the same arguments from
        ``create_module()``.
        """
        with installed_module('example', scope={'x': 3}, code='x += 1') as m:
            self.assertEquals(4, m.x)

    def test_installed_module_uninstalls_module(self):
        """
        When exiting the ``with`` block, ``ugly.module.installed_module()``
        uninstalls its module from ``sys.modules``.
        """
        with installed_module('example') as m:
            import example

        with self.assertRaises(ImportError):
            import example

    def test_adopt(self):
        """
        ``ugly.module.adopt()`` receives two arguments: a module and a "declared
        entity" (either a class or a function). It sets the ``__module__``
        attribute of the entity to the module name, if possible. If the class
        has its own declared methods the ``__module__`` attribute of them is
        also set.
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

    def test_create_module_adopts_scope_entities(self):
        """
        All classes and functions from the scope should be adopted by the module
        made by ``create_module()``.
        """
        class Class(object):
            def method(self):
                pass
        def function(a):
            pass

        m = create_module(
            'example', scope={'Class': Class, 'function': function}
        )

        self.assertEquals(m.__name__, Class.__module__)
        self.assertEquals(m.__name__, Class.method.__module__)
        self.assertEquals(m.__name__, function.__module__)

    def test_adopt_fails_on_builtins(self):
        """
        ``ugly.module.adopt()`` raises an exception if required to adopt a
        builtin.
        """
        with installed_module('example') as m:
            with self.assertRaises(AdoptException):
                adopt(m, dict)

from ugly.finder import TestFinder

load_tests = TestFinder('.', 'ugly.module.module').load_tests

if __name__ == "__main__":
    unittest.main()
