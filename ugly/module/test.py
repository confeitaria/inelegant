import unittest
import inspect

from ugly.module import create_module, installed_module

class TestModule(unittest.TestCase):

    def test_create_module(self):
        """
        ``ugly.module.create_module()`` should create a module.
        """
        m = create_module('test')

        self.assertTrue(inspect.ismodule(m))
        self.assertTrue('test', m.__name__)

    def test_create_module_scope(self):
        """
        If ``ugly.module.create_module()`` receives a dict as its ``scope``
        argument, then the values from the dict should be set into the module.
        """
        m = create_module('test', scope={'x': 3})

        self.assertEquals(3, m.x)

    def test_create_module_code(self):
        """
        If ``ugly.module.create_module()`` receives its ``code`` argument,
        then whatever it creates should be set in the module scope.
        """
        m = create_module('test', code='x = 3')

        self.assertEquals(3, m.x)

    def test_create_module_scope_code(self):
        """
        ``ugly.module.create_module()`` can receive both ``scope`` and ``code``
        arguments, in which case ``code`` can use anything from the scope.
        """
        m = create_module('test', scope={'x': 3}, code='x += 1')

        self.assertEquals(4, m.x)
