import unittest
import inspect

from ugly.module import create_module, installed_module

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

