# coding: utf-8
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

import contextlib
import imp
import sys
import inspect
import textwrap
import importlib
import os.path
import shutil
import tempfile

from inelegant.dict import temp_key
from inelegant.fs import existing_dir, temp_file, temp_dir
from inelegant.toggle import Toggle

create_module_installs_module = Toggle()
available_resource_uses_path_as_where = Toggle()


def create_module(name, code='', scope=None, to_adopt=(), defs=None):
    """
    This function creates a module::

    >>> create_module('my_module')
    <module 'my_module' (built-in)>

        **Note**: Up to inelegant 0.9.0, the function used to make the module
        importable. It is not the case anymore::

        >>> import my_module
        Traceback (most recent call last):
          ...
        ImportError: No module named my_module

        Ideally, you should use ``installed_module()`` to make it available
        to import. However, if you still need the old behavior from
        ``create_module()``, use the ``create_module_installs_module`` toggle::

        >>> with create_module_installs_module:
        ...     m = create_module('deprecated_installed_module')
        ...     import deprecated_installed_module
        ...     m == deprecated_installed_module
        True


    Executing code
    --------------

    You can give the code of the module to it::

    >>> with_code = create_module('with_code', code='x = 3')
    >>> with_code.x
    3

    The block of code can be indented (very much like doctests)::

    >>> with_code = create_module('with_code', code='''
    ...                                         x = 3
    ...                                         y = x+3
    ... ''')
    >>> with_code.x
    3
    >>> with_code.y
    6

    Defining classes and functions
    ------------------------------

    Most of the time, one wants to define functions and classes inside a
    module, but putting them into a block of code can be cumbersome. One can,
    then, define them externally and pass them as the ``to_adopt`` argument::

    >>> def function():
    ...     pass
    >>> class Class(object):
    ...     pass
    >>> m = create_module('m', to_adopt=[Class, function])
    >>> m.Class
    <class 'm.Class'>
    >>> m.function # doctest: +ELLIPSIS
    <function function at ...>

    Setting a scope
    ---------------

    It also can receive a dictionary representing a previously set up scope
    (i.e. containing values that will be set in the module)::

    >>> with_scope = create_module('with_scope', scope={'y': 32})
    >>> with_scope.y
    32

    It is possible to give both arguments as well and the code will work over
    the scope::

    >>> intricate = create_module('intricate', code='z = z+1', scope={'z': 4})
    >>> intricate.z
    5
    """
    if defs and not to_adopt:
        sys.stderr.write('Do not use defs argument, use to_adopt.')
        to_adopt = defs

    module = imp.new_module(name)

    scope = scope if scope is not None else {}
    module.__dict__.update(scope)

    adopt(module, *to_adopt)

    for d in to_adopt:
        module.__dict__[d.__name__] = d

    code = dedent(code)

    with temp_key(sys.modules, key=name, value=module):
        exec code in module.__dict__

    if create_module_installs_module.enabled:
        sys.stderr.write(
            'Installing modules on creation is deprecated but the behavior '
            'was enabled by the create_module_installs_module toggle.')

        sys.modules[name] = module

    return module


@contextlib.contextmanager
def installed_module(name, code='', to_adopt=(), scope=None, defs=None):
    """
    This is a context manager to have a module created during a context::

    >>> with installed_module('a', code='x=3', scope={'y': 4}) as m:
    ...     import a
    ...     m == a
    ...     a.x
    ...     a.y
    True
    3
    4

    On the context exit the module will be removed from ``sys.modules``::

    >>> import a
    Traceback (most recent call last):
      ...
    ImportError: No module named a
    """
    if defs and not to_adopt:
        sys.stderr.write('Do not use defs argument, use to_adopt.')
        to_adopt = defs

    module = create_module(name, code=code, to_adopt=to_adopt, scope=scope)

    with temp_key(sys.modules, key=name, value=module):
        yield module


@contextlib.contextmanager
def available_module(name, code='', extension='.py'):
    """
    Makes a module available to be imported - but does not import it.

    ``available_module() expects two arguments: the name of the module and its
    code. The name is mandatory, but the code is optional::

    >>> with available_module(name='m', code='x = 3'):
    ...     import m
    ...     m.x
    3

    Once its context is closed, the module is not available for importing
    anymore::

    >>> import m
    Traceback (most recent call last):
      ...
    ImportError: No module named m

    Differences from ``inelegant.module.installed_module()``
    ========================================================

    This function is comparable to ``installed_module()`` but its context does
    not return the module itself::

    >>> with installed_module('m') as m:
    ...     m                                           # doctest: +ELLIPSIS
    <module 'm' ...>
    >>> with available_module('m') as m:
    ...     m is None
    True

    Instead, the user should import the module. Importing the module is
    supported by ``installed_module()`` but here it is the only way to get the
    the module::

    >>> with installed_module('m'):
    ...     import m
    ...     m                                             # doctest: +ELLIPSIS
    <module 'm' ...>
    >>> with available_module('m'):
    ...     import m
    ...     m                                             # doctest: +ELLIPSIS
    <module 'm' ...>

    The argument ``code``
    =====================

    Another difference between ``installed_module()`` and
    ``available_module()`` is that the latter only accepts the ``code``
    argument - there is no ``scope`` or ``to_adopt`` argument.

    Also, the code is not executed when the module is created, but only when
    it is imported::

    >>> with available_module(name='m', code="print('During importing.')"):
    ...     print('Before importing.')
    ...     import m
    ...     print('After importing.')
    Before importing.
    During importing.
    After importing.

    This contrasts with ``installed_module()``. Since that function returns the
    module itself, the code that is passed to it should be executed before the
    importing::

    >>> with installed_module(name='m', code="print('During importing.')"):
    ...     print('Before importing?')
    ...     import m
    ...     print('After importing.')
    During importing.
    Before importing?
    After importing.

    The usefulness with faulting modules
    ====================================

    This behavior is useful when we need a module that raises an exception when
    imported, for testing purposes. With ``installed_module()``, the mere call
    of the function would raise an exception::

    >>> with installed_module(name='m', code="raise Exception()"):
    ...     print('Is this line even executed?')
    ...     try:
    ...         import m
    ...     except Exception as e:
    ...         print('The exception was handled.')
    Traceback (most recent call last):
      ...
    Exception

    Now, with ``available_module()``, the exception will only be raised in the
    importing::

    >>> with available_module(name='m', code="raise Exception()"):
    ...     print('This line is really executed!')
    ...     try:
    ...         import m
    ...     except Exception as e:
    ...         print('The exception was handled.')
    This line is really executed!
    The exception was handled.
    """
    source_name = name + extension

    with temp_dir() as tempdir,\
            temp_file(where=tempdir, name=source_name, content=code):

        sys.path.append(tempdir)

        try:
            yield
        finally:
            sys.path.remove(tempdir)
            if name in sys.modules:
                del sys.modules[name]


@contextlib.contextmanager
def available_resource(module, name=None, where=None, path=None, content=''):
    """
    ``available_resource()`` is a context manager that creates a resource
    associated with a moduled created by ``available_module()``.

    To create a resource, we need at least a module name' and the name of the
    resource file::

    >>> import pkgutil
    >>> with available_module('m'):
    ...     with available_resource('m', 'test.txt'):
    ...         pkgutil.get_data('m', 'test.txt')
    ''

    You can also give the content of the resource::

    >>> with available_module('m'):
    ...     with available_resource('m', 'test.txt', content='example'):
    ...         pkgutil.get_data('m', 'test.txt')
    'example'

    Once the context is done, the resource is gone::

    >>> with available_module('m'):
    ...     with available_resource('m', 'test.txt'):
    ...         pass
    ...     pkgutil.get_data('m', 'test.txt') # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    IOError: ...

    The ``where`` and ``path`` arguments
    ====================================

    If needed, one can define the directory where the resource will be. One
    just needs to use the ``where`` argument::

    >>> with available_module('m'):
    ...     with available_resource(
    ...             'm', 'test.txt', where='a', content='test'):
    ...         pkgutil.get_data('m', 'a/test.txt')
    'test'

    If one has the path of the resource, one can give it directly to the
    context manager via the ``path`` argument::

    >>> with available_module('m'):
    ...     with available_resource(
    ...             'm', path='a/test.txt', content='test'):
    ...         pkgutil.get_data('m', 'a/test.txt')
    'test'

        **Note:** Up to inelegant 0.1.0, the ``path`` argument used to be
        prefixed to the ``name`` argument to generate the path, and there was
        no ``where`` argument. If you are dependent on this behavior, it can be
        enabled via the ``available_resource_uses_path_as_where`` toggle:

        >>> with available_resource_uses_path_as_where:
        ...     with available_module('m'):
        ...         with available_resource(
        ...                 'm', 'test.txt', path='a', content='test'):
        ...             pkgutil.get_data('m', 'a/test.txt')
        'test'
    """
    if available_resource_uses_path_as_where.enabled:
        sys.stderr.write(
            'Using the "path" argument as a component to be prefixed to the '
            '"name" argument is deprecated but this behavior was enabled by '
            'the available_resource_uses_path_as_where toggle.')

        if where is not None:
            raise TypeError(
                'available_resource() does not accept "where" argument if it '
                'is using "path" as component of the file path.')

        if path is None:
            path = ''

        path = os.path.join(path, name)

    if path is None:
        if where is None:
            where = ''
        path = os.path.join(where, name)

    module = importlib.import_module(module)
    module_path = os.path.dirname(module.__file__)
    filename = os.path.join(module_path, path)

    with existing_dir(os.path.dirname(filename)):
        with temp_file(path=filename, content=content):
            yield


def adopt(module, *entities):
    """
    When a module "adopts" a class or a function, the ``__module__`` attribute
    of the given class or function is set to the name of the module. For
    example, if we have a class as the one below::

    >>> class Example(object):
    ...     def method(self):
    ...         pass

    Then it will have its ``__module__`` values set to the name of the module
    below::

    >>> with installed_module('example') as m:
    ...     adopt(m, Example)
    ...     Example.__module__
    ...     Example.method.__module__
    'example'
    'example'

    This function can adopt many values at once as well::

    >>> def function():
    ...     pass
    >>> with installed_module('example') as m:
    ...     adopt(m, Example, function)
    ...     Example.__module__
    ...     function.__module__
    'example'
    'example'

    The main reason for adopting classes and functions is to run their
    doctests.

    ::

    >>> import doctest, unittest
    >>> class Adopted(object):
    ...     '''
    ...     >>> 3+3
    ...     6
    ...     '''
    >>> class NonAdopted(object):
    ...     '''
    ...     >>> 3+3
    ...     FAIL
    ...     '''

    If a module is given to ``doctest.DocTestSuite``, only docstrings from the
    classes and routines from the given module are going to be executed. By
    adopting entities from other modules, a module tiven to ``DocTestSuite``
    will have these foreign entities' doctests executed as well::

    >>> with installed_module('m') as m:
    ...     m.Adopted = Adopted
    ...     m.NonAdopted = NonAdopted
    ...     adopt(m, Adopted)
    ...     suite = doctest.DocTestSuite(m)
    ...     result = unittest.TestResult()
    ...     result = suite.run(result)
    ...     result.testsRun
    ...     len(result.failures)
    ...     len(result.errors)
    1
    0
    0
    """
    unadoptable = [e for e in entities if not is_adoptable(e)]
    if unadoptable:
        raise AdoptException(*unadoptable)

    for entity in entities:
        entity = get_adoptable_value(entity)

        if inspect.isclass(entity):
            for a in get_adoptable_attrs(entity):
                adopt(module, a)

        entity.__module__ = module.__name__


def get_adoptable_value(obj):
    """
    Methods by themselves are not adoptable, but their functions are. This
    function will check whether an object is a method. If it is not, it will
    return the object itself::

    >>> class Class(object):
    ...     def m(self):
    ...         pass
    >>> get_adoptable_value(Class)
    <class 'inelegant.module.Class'>
    >>> def f():
    ...     pass
    >>> get_adoptable_value(f) # doctest: +ELLIPSIS
    <function f at ...>

    If it is a method, however, it will return the function "enveloped" by it::

    >>> get_adoptable_value(Class.m) # doctest: +ELLIPSIS
    <function m at ...>
    """
    if inspect.ismethod(obj):
        return obj.im_func
    else:
        return obj


def get_adoptable_attrs(obj):
    """
    Get all attributes from the object which can be adopted::

    >>> class Example(object):
    ...     def method(self):
    ...         pass
    ...     class Inner(object):
    ...         pass
    ...     value = 3
    ...     builtin = dict
    >>> adoptable = list(get_adoptable_attrs(Example))
    >>> len(adoptable)
    2
    >>> Example.method in adoptable
    True
    >>> Example.Inner in adoptable
    True
    >>> Example.builtin in adoptable
    False
    >>> Example.value in adoptable
    False
    """
    attrs = (getattr(obj, n) for n in dir(obj))
    return (
        a for a in attrs
        if is_adoptable(a) and a.__module__ == obj.__module__
    )


def is_adoptable(obj):
    """
    Checks whether an object is adoptable - i.e., whether such an object can
    have its ``__module__`` attribute set.

    To be adoptable, an object should have a ``__module__`` attribute. In
    general, functions and classes satisfies these criteria::

    >>> class Example(object): pass
    >>> def f(a): pass
    >>> is_adoptable(Example)
    True
    >>> is_adoptable(f)
    True
    >>> is_adoptable(3)
    False

    Any object with these properites, however, would be adoptable::

    >>> e = Example()
    >>> e.__module__ = ''
    >>> is_adoptable(e)
    True

    Some classes and functions have read-only ``__module__`` attributes. Those
    are not adoptable::

    >>> is_adoptable(dict)
    False
    """
    obj = get_adoptable_value(obj)

    conditions = [
        hasattr(obj, '__module__'),
        is_module_rewritable(obj)
    ]

    return all(conditions)


def is_module_rewritable(obj):
    """
    Checks whether the ``__module__`` attribute of the object is rewritable::

    >>> def f():
    ...     pass
    >>> is_module_rewritable(f)
    True
    >>> is_module_rewritable(dict)
    False
    """
    try:
        obj.__module__ = obj.__module__
        return True
    except:
        return False


class AdoptException(ValueError):
    """
    Exception raised when trying to make a module to adopt an unadoptable
    object, such as one that is not a function or object...

    ::

    >>> with installed_module('m') as m:
    ...     adopt(m, 3)
    Traceback (most recent call last):
        ...
    AdoptException: 3 has no __module__ attribute.

    ...or a built-in function::

    >>> with installed_module('m') as m:
    ...     adopt(m, dict)
    Traceback (most recent call last):
        ...
    AdoptException: <type 'dict'> __module__ attribute is ready-only.

    It can also receive more than one value::

    >>> with installed_module('m') as m:
    ...     adopt(m, dict, 3)
    Traceback (most recent call last):
        ...
    AdoptException: <type 'dict'> __module__ attribute is ready-only.
        3 has no __module__ attribute.
    """

    def __init__(self, *objs):
        messages = []
        for obj in objs:
            if not hasattr(obj, '__module__'):
                messages.append(
                    "{0} has no __module__ attribute.".format(repr(obj))
                )
            elif not is_module_rewritable(obj):
                messages.append(
                    "{0} __module__ attribute is ready-only.".format(repr(obj))
                )

        if messages:
            Exception.__init__(self, "\n    ".join(messages))
        else:
            Exception.__init__(self)


def get_caller_module(index=1):
    """
    ``get_caller_module()`` returns the module from where a specific frame from
    the frame stack was called.

    A throughout explanation
    ------------------------

    Let's suppose it is called inside a function defined in a module ``a`` that
    is called by a function defined in a module ``b``, which is called by a
    function defined in a module ``c``:

    - if it ``get_caller_module()`` module is called with the index 0, it will
    return the ``a`` module;
    - if it is called with index 1, it will return the ``b`` module;
    - and if its index is 2, it will return the ``c`` module.

    Something like this:

    2 - c
    1   └ b
    0     └ a
            └ get_caller_module()

    Here is a working example::

    >>> from inelegant.module import installed_module
    >>> scope_a = {'get_caller_module': get_caller_module}
    >>> code_a = '''
    ...     def f_a():
    ...         print get_caller_module(0)
    ...         print get_caller_module(1)
    ...         print get_caller_module(2)
    ...     '''
    >>> with installed_module('a', code=code_a, scope=scope_a):
    ...     code_b = '''
    ...         import a
    ...         def f_b():
    ...             a.f_a()
    ...     '''
    ...     with installed_module('b', code=code_b):
    ...         code_c = '''
    ...             import b
    ...             def f_c():
    ...                 b.f_b()
    ...         '''
    ...         with installed_module('c', code=code_c) as c:
    ...             c.f_c() # doctest: +ELLIPSIS
    <module 'a' ...>
    <module 'b' ...>
    <module 'c' ...>

    The default index
    -----------------

    The index, however, is optional: ``get_caller_module()`` by default uses
    the index 1.

    It may be counterintuitive at first - why not zero? But it is a more useful
    default. The function will rarely be called to discover in which module it
    is being called because _it is already there_. Most of the time one will
    want to discover where _the function which called ``get_caller_module()``
    was called.

    For example, we could have the following function::

    >>> def print_current_module():
    ...     print get_caller_module()

    Were the default index 0, it would print the module where
    ``get_current_module()`` was defined. However, we want the module where it
    was _called_ - and this is a level higher::

    >>> scope = {'print_current_module': print_current_module}
    >>> with installed_module('m', code='print_current_module()', scope=scope):
    ...     pass # doctest: +ELLIPSIS
    <module 'm' ...>

    If ``get_caller_module()`` could explain its default index to its calling
    module itself, it would say:

        I don't tell you who you are - you already know that. I tell you who
        is calling you ;)
    """
    frame = sys._getframe(index+1)

    return importlib.import_module(frame.f_globals['__name__'])


def dedent(code):
    """
    Remove any consistent indentation found in a string. For example, consider
    the block below::

    >>> a = '''
    ...         for i in range(10):
    ...             print i
    ... '''
    >>> a
    '\\n        for i in range(10):\\n            print i\\n'

    When dendented, it will look like this::

    >>> dedent(a)
    'for i in range(10):\\n    print i\\n'
    """
    if isinstance(code, basestring) and code.startswith('\n'):
        code = code.replace('\n', '', 1)

    return textwrap.dedent(code)
