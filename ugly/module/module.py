# coding: utf-8
import contextlib
import imp
import sys
import inspect
import textwrap
import importlib

def create_module(name, code='', scope=None, defs=()):
    """
    This function creates a module and adds it to the available ones::

    >>> m = create_module('my_module')
    >>> import my_module
    >>> my_module == m
    True

    You can give the code of the module to it::

    >>> m = create_module('with_code', code='x = 3')
    >>> import with_code
    >>> with_code.x
    3

    It also can receive a dictionary representing a previously set up scope
    (i.e. containing values that will be set in the module)::

    >>> m = create_module('with_scope', scope={'y': 32})
    >>> import with_scope
    >>> with_scope.y
    32

    It is possible to give both arguments as well and the code will work over
    the scope::

    >>> m = create_module('intricate', code='z = z+1', scope={'z': 4})
    >>> import intricate
    >>> intricate.z
    5
    """
    scope = scope if scope is not None else {}
    if isinstance(code, basestring) and code[:1] == '\n':
        code = code[1:]
    code = textwrap.dedent(code)

    module = imp.new_module(name)
    sys.modules[name] = module
    module.__dict__.update(scope)

    for v in defs:
        if is_adoptable(v):
            module.__dict__[v.__name__] = v
            adopt(module, v)

    exec code in module.__dict__

    return module

@contextlib.contextmanager
def installed_module(name, code='', defs=(), scope=None):
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
    yield create_module(name, code=code, defs=defs, scope=scope)
    del sys.modules[name]

def adopt(module, entity):
    """
    When a module "adopts" a class or a function, the ``__module__`` attribute
    of the given class or function is set to the name of the module. For
    example, if we have a class as the one below::

    >>> class Example(object):
    ...     def method(self):
    ...         pass

    Then it will have its ``__module__`` values set to the name of the modul ebelow

    >>> with installed_module('example') as m:
    ...     adopt(m, Example)
    ...     Example.__module__
    ...     Example.method.__module__
    'example'
    'example'
    """
    if not is_adoptable(entity):
        raise AdoptException(entity)

    if inspect.isclass(entity):
        for a in get_adoptable_attrs(entity):
            adopt(module, a)
    elif inspect.ismethod(entity):
        entity = entity.im_func

    entity.__module__ = module.__name__

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
    attrs = ( getattr(obj, n) for n in dir(obj) )
    return (
        a
            for a in attrs
            if is_adoptable(a) and a.__module__ == obj.__module__
    )

def is_adoptable(obj):
    """
    Checks whether an object is adoptable. Adoptable objects are basically
    classes and functions::

    >>> class Example(object): pass
    >>> def f(a): pass
    >>> is_adoptable(Example)
    True
    >>> is_adoptable(f)
    True
    >>> is_adoptable(Example())
    False

    Built-in classes and functions are not adoptable, though::

    >>> is_adoptable(dict)
    False
    """
    return is_adoptable_type(obj) and not is_builtin(obj)

def is_adoptable_type(obj):
    """
    Checks whether an object is of an adoptable type - a class, a function or a
    method::

    >>> class Example(object):
    ...     def method(self):
    ...         pass
    >>> def f(a): pass
    >>> is_adoptable_type(Example)
    True
    >>> is_adoptable_type(Example.method)
    True
    >>> is_adoptable_type(f)
    True
    >>> is_adoptable_type(Example())
    False
    """
    return (
        inspect.isclass(obj) or inspect.isfunction(obj) or inspect.ismethod(obj)
    )

def is_builtin(obj):
    """
    Checks whether an object is built-in - either is a built-in function or
    belongs to the ``builtin`` module::

    >>> class Example(object): pass
    >>> is_builtin(Example)
    False
    >>> is_builtin(dict)
    True
    """
    return inspect.isbuiltin(obj) or obj.__module__ == '__builtin__'

class AdoptException(Exception):
    """
    Exception raised when trying to make a module to adopt an unadoptable
    object, such as one that is not a function or object...

    ::

    >>> with installed_module('m') as m:
    ...     adopt(m, 3)
    Traceback (most recent call last):
        ...
    AdoptException: 'int' values such as 3 are not adoptable.

    ...or a built-in function::

    >>> with installed_module('m') as m:
    ...     adopt(m, dict)
    Traceback (most recent call last):
        ...
    AdoptException: 'dict' is not adoptable because it is a builtin.
    """

    def __init__(self, obj=None):
        if obj is None:
            message = None
        elif not is_adoptable_type(obj):
            message = "'{0}' values such as {1} are not adoptable.".format(
                type(obj).__name__, str(obj)
            )
        elif is_builtin(obj):
            message = "'{0}' is not adoptable because it is a builtin.".format(
                obj.__name__
            )

        if message is not None:
            Exception.__init__(self, message)
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

    >>> from ugly.module import installed_module
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

    The index, however, is optional: ``get_caller_module()`` by default uses the
    index 1.

    It may be counterintuitive at first - why not zero?. But it is a more useful
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
    """
    frame = sys._getframe(index+1)

    return importlib.import_module(frame.f_globals['__name__'])
