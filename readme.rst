=================================================
Inelegant, a directory of weird helpers for tests
=================================================

or

=======================================
Inelegant: better ugly than unavailable
=======================================

.. Copyright 2015, 2016 Adam Victor Brandizzi

Inelegant groups a series of tools that are very useful for automating tests.
Most of them are unreliable or costly "in the wild" but can be useful enough on
tests.

Right now there are nine modules in this project.

"Inelegant Process" - running and communicating with a simple processes
=======================================================================

This module contains the class ``inelegant.process.Process``. This class
extends ``multiprocessing.Process`` so one can easily recover information sent
by the target.

Returned values and exceptions
------------------------------

For example, one can get the returned value::

    >>> from inelegant.process import Process
    >>> def invert(n):
    ...     return 1.0/n
    >>> process = Process(target=invert, args=(2.0,))
    >>> process.start()
    >>> process.join() # The value is only available after the process end.
    >>> process.result
    0.5

If the process is finished by an exception, it can also be retrieved::

    >>> process = Process(target=invert, args=(0.0,))
    >>> process.start()
    >>> process.join()
    >>> process.exception
    ZeroDivisionError('float division by zero',)

Getting and sending data
------------------------

If the target function is a generator function, then one can send values to and
receive values from it with the ``Process.send()`` and ``Process.get()``.
However, we have a limitation here: one should *always* send a value after
getting one, and ``get()`` will return *all* yielded values at each call, even
if they are useless::

    >>> def add():
    ...     a = yield
    ...     b = yield
    ...     yield a+b
    >>> process = Process(target=add)
    >>> process.start()
    >>> process.send(1)
    >>> process.send(2)
    >>> process.get() # First yield statement gave us nothing so it is None here
    >>> process.get() # Same with second yield
    >>> process.get() # Finally, the value
    3
    >>> process.send(None) # Necessary to continue
    >>> process.join()

The last ``send()`` call can be replaced with the ``go()`` method.

(This is not a very intuitive contract but proved itself very useful.)

As a context manager
--------------------

A very nice feature of ``inelegant.process.Process`` is that it is a context
manager. If one is given to a ``with`` statement, it is guaranteed that it will
be finished after the block ends. This is useful because it is too easy to
forget to join a process. If it happens, we have problems::

    >>> process = Process(target=invert, args=(4,))
    >>> process.start()
    >>> process.result + 3 # Oops, the value is not available yet!
    Traceback (most recent call last):
      ...
    TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
    >>> process.join() # Alas, it is too late.

Using the ``with`` statement it is done automatically and without way less
clutter. The process starts itself before proceeding and is joined once the
block ends. The parent process will wait for its child's end after the block::

    >>> with Process(target=invert, args=(4,)) as process:
    ...     pass
    >>> process.result
    0.25

    >>> process = Process(target=invert, args=(0.0,))
    >>> process.start()
    >>> process.join()

Automatic process termination
-----------------------------

By default, ``Process`` assume the target function will finish itself
eventually, but it may execute indefinitely. In these cases, you may want to
just kill the process once the ``with`` block is done. Then, just set the
``terminate`` argument of ``Process`` constructor::

    >>> def forever():
    ...     while True: pass
    >>> with Process(target=forever, terminate=True) as process:
    ...     pass
    >>> process.is_alive()
    False

In general, however, it is better to write a function that finishes itself.

(Note that, if an exception is raised ending the ``with`` block, the subprocess
is killed as well, since we do not know if it would need more information to
proceed with its execution.)

Raising subprocess exceptions at the parent process
---------------------------------------------------

Let us suppose an exception ended our subprocess. Having the exception available
at ``Process.exception`` is useful, indeed, but not very practical to examine
most of the time. Fortunately, it can be raised again. Just set the
``reraise`` argument of the constructor and any exception will be re-raised once
the subprocess is joined::

    >>> process = Process(target=invert, args=(0.0,), reraise=True)
    >>> process.start()
    >>> process.join()
    Traceback (most recent call last):
      ...
    ZeroDivisionError: float division by zero

Since the process is joined after the block if given to a ``with`` statement,
children exceptions would also be raised - but only after the block finishes::

    >>> with Process(target=invert, args=(0.0,), reraise=True):
    ...     executed = True
    Traceback (most recent call last):
      ...
    ZeroDivisionError: float division by zero
    >>> executed
    True

"Inelegant Net" - quick and dirty network tricks
================================================

The module ``inelegant.net`` provides tools for easing testing some very simple
network communication code.

The ``Server`` class
--------------------

For example, it has the ``inelegant.Server``, a subclass of
``SocketServer.TCPServer`` that only serves a string in a specific port::

    >>> from inelegant.net import Server
    >>> server = Server('localhost', 9000, message='my message')
    >>> import contextlib, socket, time
    >>> with Process(target=server.handle_request):
    ...     time.sleep(0.1)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         s.connect(('localhost', 9000))
    ...         s.recv(10)
    b'my message'

However, it is probably best used as a context manager. If given to a ``with``
statement, the server will be started alone in the background and finished once
the block is exited::

    >>> with Server('localhost', 9000, message='my message'):
    ...     time.sleep(0.1)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         s.connect(('localhost', 9000))
    ...         s.recv(10)
    b'my message'
    >>> with contextlib.closing(socket.socket()) as s:
    ...     s.connect(('localhost', 9000))
    Traceback (most recent call last):
      ...
    ConnectionRefusedError: [Errno 111] Connection refused

Waiter functions
----------------

To be honest, the ``Server`` class is mostly used to test the reason of the
Inelegant Net: the waiter functions.

These functions wait for a port to be up or down in a specific host. There are
two of them:

``wait_server_up(host, port)``
    Blocks until there is a process listening at the given port from the given
    host. Useful when we want to do something only when a server is already up
    and running.

    It is not uncommon a server can take a bit of time to start due to resource
    loading etc. For example, consider the example we saw below. If we remove
    the waiting time from the second line, it will probably fail::

        >>> with Server('localhost', 9000, message='my message'):
        ...     time.sleep(0.01)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         s.connect(('localhost', 9000))
        ...         s.recv(10)
        b'my message'

    The problem is, these wait times are wasteful: to ensure the server is up,
    we wait way more time than it is necessary most of the times. It is
    unreliable, too, because there will be always a time when the waiting time
    is not enough.

    With ``wait_server_up()``, the process waits only for the necessary amount
    of time - and no more::

        >>> from inelegant.net import wait_server_up
        >>> start = time.time()
        >>> with Server('localhost', 9000, message='my message'):
        ...     wait_server_up('localhost', 9000)
        ...     time.time() - start < 0.01
        True

    It has a timeout: by default, it will not wait more than one second and, if
    the server is not up, an exception is raised. It can be made longer with
    the ``timeout`` argument::

        >>> start = time.time()
        >>> with Server('localhost', 9000):
        ...     wait_server_up('localhost', 9000, timeout=60)
        ...     time.time() - start < 0.01
        True


``wait_server_down()``
    Likewise, it is common to have to wait for a server being down on a
    specific port. Again, it is common to rely on waiting times. Consider the
    hypotetical server below::

        >>> def slow_server():
        ...     with Server('localhost', 9000) as server:
        ...         yield
        ...         time.sleep(0.01)
        ...         server.shutdown()

    If we start and shutdown it, and then try to bound to the same port, it
    will likely fail::

        >>> with Process(target=slow_server) as p:
        ...     wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         s.bind(('localhost', 9000))
        Traceback (most recent call last):
         ...
        OSError: [Errno 98] Address already in use

    A common solution is to add some wait time::

        >>> with Process(target=slow_server) as p:
        ...     wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         time.sleep(0.02)
        ...         s.bind(('localhost', 9000))

    Again, it is a suboptimal. Generally, the wait time is way larger
    than needed most of the time, and even in this situation it will fail
    sometimes.. With ``wait_server_down()``, the client can block itself until
    the server is not running anymore - and no more::

        >>> from inelegant.net import wait_server_up, wait_server_down
        >>> with Process(target=slow_server) as p:
        ...     wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         wait_server_down('localhost', 9000)
        ...         s.bind(('localhost', 9000))

    It will wait for at most one second by default, but the timeout can be
    changed::

        >>> with Process(target=slow_server) as p:
        ...     wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         wait_server_down('localhost', 9000, timeout=60)
        ...         s.bind(('localhost', 9000))

"Inelegant Module" - creating modules
=====================================

With ``inelegant.module`` one can create and import modules at runtime, without
needing to write a file.

The ``create_module()`` function
--------------------------------

To create a module, one can use the ``create_module()`` function. The function
has a mandatory argument, the module name::

    >>> from inelegant.module import create_module
    >>> create_module('m') # doctest: +ELLIPSIS
    <module 'm'>

Note, however, that creating a module does not make it available for
importing::

    >>> import m
    Traceback (most recent call last):
      ...
    ModuleNotFoundError: No module named 'm'

Giving scope, definitions and code to the module
------------------------------------------------

An empty module is not very useful, so ``create_module()`` provides some ways
of putting stuff on it. She simplest one is probably the ``scope`` argument. It
should be a dictionary, and every value from it will be attributed to a variable
whose name is its key::

    >>> m = create_module('m', scope={'x': 3})
    >>> m.x
    3

Modules can also define classes and functions. Such entities, when defined on a
module, will have a ``__module__`` attribute set. If one passes these entities
through the scopes dict, however, the module name will not have it set::

    >>> class Class(object):
    ...     pass
    >>> m = create_module('m', scope={'Class': Class})
    >>> m.Class.__module__ == 'm'
    False

 One should pass them through the ``to_adopt`` argument (which should be
 iterable) to have the classes and functions "adopted" by the module::

    >>> m = create_module('m', to_adopt=[Class])
    >>> m.Class.__module__
    'm'

Finally, sometimes it is more practical to just pass a bunch of code to be
executed as the module source. In these cases, the ``code`` attribute should be
used::

    >>> m = create_module('m', scope={'x': 3}, code="""
    ...     y = x+1
    ... """)
    >>> m.x
    3
    >>> m.y
    4

As you can see, the values from the scope dict are available to the code being
executed.

The ``installed_module()`` context manager
------------------------------------------

While it may be useful to create a module by itself, many times we want to be
able to import them as well. In tests, we usually want to make it available for
importing only temporarily. IN this cases, we can use the
``installed_module()`` functions. It receives exactly the same arguments from
``create_module()`` but returns a context manager. If given to a ``with``
statement, the module will be available for importing...

::

    >>> from inelegant.module import installed_module
    >>> with installed_module('some_module', scope={'x': 3}) as m:
    ...     import some_module
    ...     m == some_module
    True

...but only inside the ``with`` block::

    >>> import some_module
    Traceback (most recent call last):
      ...
    ModuleNotFoundError: No module named 'some_module'

The ``available_module()`` context manager
------------------------------------------

Makes a module available to be imported - but does not import it.

``available_module() expects two arguments: the name of the module and its
code. The name is mandatory, but the code is optional::

    >>> from inelegant.module import available_module
    >>> with available_module(name='m', code='x = 3'):
    ...     import m
    ...     m.x
    3

Once its context is closed, the module is not available for importing
anymore::

    >>> import m
    Traceback (most recent call last):
      ...
    ModuleNotFoundError: No module named 'm'

It is similar ``installed_module()`` but its context does not return the module
itself::

    >>> with installed_module('m') as m:
    ...     m                                           # doctest: +ELLIPSIS
    <module 'm'>
    >>> with available_module('m') as m:
    ...     m is None
    True

Instead, the user should necessarily import the module.

Also, the code is not executed when the module is created, but only when it is
imported::

    >>> with available_module(name='m', code="print('During importing.')"):
    ...     print('Before importing.')
    ...     import m
    ...     print('After importing.')
    Before importing.
    During importing.
    After importing.
    >>> with installed_module(name='m', code="print('During importing.')"):
    ...     print('Before importing?')
    ...     import m
    ...     print('After importing.')
    During importing.
    Before importing?
    After importing.

This behavior is useful when we need a module that raises an exception when
imported.

The ``available_resource`` function
-----------------------------------

Another thing we can only do with available modules (for now) is to add
resource files to them. We do it with the ``available_resource()`` function.

As much as ``available_module()``, ``available_resource()`` is a context
manager. It expects at least the name of the module and the name of the
resource file::

    >>> from inelegant.module import available_resource
    >>> import pkgutil
    >>> with available_module('m'):
    ...     with available_resource('m', 'my-file.txt'):
    ...         pkgutil.get_data('m', 'my-file.txt')
    b''

Since we want to put content on these resources, we can give it to the function
with the ``content`` argument::

    >>> with available_module('m'):
    ...     with available_resource('m', 'my-file.txt', content='example'):
    ...         pkgutil.get_data('m', 'my-file.txt')
    b'example'

Once the ``available_resource()`` context ends, the resource is not available
anymore::

    >>> with available_module('m'):
    ...     with available_resource('m', 'my-file.txt', content='example 2'):
    ...         assert pkgutil.get_data('m', 'my-file.txt') == b'example 2'
    ...     pkgutil.get_data('m', 'my-file.txt') # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    FileNotFoundError: ...

The ``get_caller_module()`` function
------------------------------------

Finally, ``inelegant.module`` provides the ``get_caller_module()`` function. It
basically returns the module from where the current function was called.

For example, suppose we have a module ``m1`` with a function ``f()``::

    >>> from inelegant.module import get_caller_module
    >>> def f():
    ...     print(get_caller_module())

``m2`` imports ``m1`` and call it. What will it return? It will return ``m2``
since it is the module calling ``f()``::

    >>> with installed_module('m1', to_adopt=[f]),\
    ...         installed_module('m2', code='import m1; m1.f()'):
    ...     pass # doctest: +ELLIPSIS
    <module 'm2'>

As we like to put it, ``get_caller_module()`` doesn't tell you who you are - you
already know that. I tell you who is calling you.

That said, ``get_caller_module()`` accepts an index as its argument. In this
case, it will return the n-th module from the frame stack, being 0 the module
where ``get_caller_module()`` was called. Basically, it means the default value
of the index is 1::

    >>> def f2():
    ...     print(get_caller_module(1))
    >>> with installed_module('m1', to_adopt=[f2]),\
    ...         installed_module('m2', code='import m1; m1.f2()'):
    ...     pass # doctest: +ELLIPSIS
    <module 'm2'>

The ``temp_var()`` context manager and decorator
------------------------------------------------

``inelegant.module.temp_var()`` returns a context manager that temporarily sets
a variable into a module::

    >>> from inelegant.module import temp_var
    >>> a = create_module('a', scope={'var': 1})
    >>> with temp_var(a, 'var', 2):
    ...    a.var
    2

Once the context manager is done, the variable should have the old value::

    >>> a.var
    1

If the variable does not exist before...

    ::

        >>> with temp_var(a, 'new', 10):
        ...    a.new
         10

...it should not exist after::

    >>> a.new
    Traceback (most recent call last):
      ...
    AttributeError: module 'a' has no attribute 'new'

You can also only pass the module name to ``temp_var()``::

    >>> with available_module('b', code='var = 1'):
    ...    with temp_var('b', 'var', 2):
    ...        import b
    ...        print('temporary var in b:', b.var)
    ...    print('default var in b:', b.var)
    temporary var in b: 2
    default var in b: 1

The context manager also behaves like a decorator::

    >>> with installed_module('c', scope={'var': 1}) as c:
    ...    @temp_var(c, 'var', 2)
    ...    def f():
    ...        print(c.var)
    ...    f()
    ...    c.var
    2
    1

"Inelegant Finder": straightforward way of finding test cases
=============================================================

Finally, we have ``inelegant.finder.TestFinder``, a ``unittest.TestSuite``
subclass that finds tests by itself.

Finding tests in modules
------------------------

``TestFinder`` can receive an arbitrary number of modules as its constructor
arguments. The finder will then find every test case from these modules, as
well as any doctests in docstrings from it.

Consider the definitions below::

    >>> import unittest
    >>> def add(a, b):
    ...     """
    ...     Sums two values:
    ...
    ...     >>> add(2, 2)
    ...     FAIL
    ...     """
    ...     return a + b
    >>> class TestAdd(unittest.TestCase):
    ...     def test22(self):
    ...         self.assertEqual(3, add(2, 2))

We can put them on modules and give the modules to test finder. Both the
doctest and the unit test will be called when the finder suite be executed::

    >>> from inelegant.finder import TestFinder
    >>> with installed_module('a', to_adopt=[add]) as a,\
    ...         installed_module('ta', to_adopt=[TestAdd]) as ta:
    ...     finder = TestFinder(a, ta)
    ...     import sys
    ...     runner = unittest.TextTestRunner(stream=sys.stdout)
    ...     runner.run(finder) # doctest: +ELLIPSIS
    FF
    ...
    Failed example:
        add(2, 2)
    Expected:
        FAIL
    Got:
        4
    ...
    FAIL: test22 (ta.TestAdd)
    ...
    AssertionError: 3 != 4
    ...
    <unittest.runner.TextTestResult run=2 errors=0 failures=2>

We do not even need to import the modules - it is possible to just pass their
names::

    >>> with installed_module('a', to_adopt=[add]),\
    ...         installed_module('ta', to_adopt=[TestAdd]):
    ...     finder = TestFinder('a', 'ta')
    ...     import os
    ...     with open(os.devnull, 'w') as devnull:
    ...         runner = unittest.TextTestRunner(stream=devnull)
    ...         runner.run(finder) # doctest: +ELLIPSIS
    <unittest.runner.TextTestResult run=2 errors=0 failures=2>

Loading doctests in files
-------------------------

The ``TestFinder`` also accepts file paths (or even file objects) as its
arguments. In this case, the file is expected to be a text file containing
doctests (like yours truly, indeed).

Another good example would be the file created below::

    >>> import tempfile
    >>> _, path = tempfile.mkstemp()
    >>> with open(path, 'w') as f:
    ...     _ = f.write('''
    ...         >>> 2+2
    ...         3
    ...     ''')

We just need to give the path to the finder::

    >>> finder = TestFinder(path)
    >>> runner = unittest.TextTestRunner(stream=sys.stdout)
    >>> runner.run(finder) # doctest: +ELLIPSIS
    F
    ...
    File "...", line 2, in ...
    Failed example:
        2+2
    Expected:
        3
    Got:
        4
    ...
    FAILED (failures=1)
    <unittest.runner.TextTestResult run=1 errors=0 failures=1>
    >>> os.remove(path)

The file path can be either relative or absolute. If it is not absolute, it
will be relative to the module where ``TestFinder`` was instantiated.

The ``load_tests()`` method
---------------------------

Python's ``unittest`` has this nice feature named "`load_tests protocol`__". To
understand it, one should know that ``TestLoader.loadTestsFromModule()`` looks
for all subclasses of ``unittest.TestCase`` inside the modules given to it:

__ https://docs.python.org/2/library/unittest.html#load-tests-protocol

::

    >>> class TestCase1(unittest.TestCase):
    ...     def test1(self):
    ...         self.assertEqual(1, 1)
    >>> class TestCase2(unittest.TestCase):
    ...     def test2(self):
    ...         self.assertEqual(2, 1)
    >>> with installed_module('t', to_adopt=[TestCase1,TestCase2]) as t:
    ...     finder = TestFinder('t')
    ...     loader = unittest.TestLoader()
    ...     suite = loader.loadTestsFromModule(t)
    ...     with open(os.devnull, 'w') as devnull:
    ...         runner = unittest.TextTestRunner(stream=devnull)
    ...         runner.run(finder)
    <unittest.runner.TextTestResult run=2 errors=0 failures=1>

We can change this default behavior by defining a function called
``load_tests()`` in the module. This function receives three arguments: an
``unittest.TestLoader`` instance, a test suite with all tests found in the
module, and a pattern to match files (only really useful when loading tests
from packages). ``load_tests()`` should itself return a test suite - and this
test suite will be the one returned by ``loadTestsFromModule()``. With this,
one can customize which tests are loaded from the module. For example, the code
below will only run ``TestCase1``, although there are two test cases in the
module::

    >>> def load_tests(loader, tests, pattern):
    ...     # We merely ignore the given tests.
    ...     suite = unittest.TestSuite()
    ...     suite.addTest(loader.loadTestsFromTestCase(TestCase1))
    ...     return suite
    >>> with installed_module(
    ...         't', to_adopt=[TestCase1, TestCase2, load_tests]
    ...     ) as t:
    ...     finder = TestFinder('t')
    ...     loader = unittest.TestLoader()
    ...     suite = loader.loadTestsFromModule(t)
    ...     with open(os.devnull, 'w') as devnull:
    ...         runner = unittest.TextTestRunner(stream=devnull)
    ...         runner.run(finder)
    <unittest.runner.TextTestResult run=1 errors=0 failures=0>

For its turn, ``TestFinder`` has a method called ``load_tests()`` that merely
returns the finder instance itself - also, it accepts the three expected
arguments. So, if you want the automatic test discoverers (such as
``unittest.TestLoader.loadTestsFromModule()``) to load all tests found by
``TestFinder`` in a module, you just need to assign the instance's
``load_tests()`` method to the ``load_tests`` module variable.

So, consider the function and class defined below::

    >>> def add(a, b):
    ...     """
    ...     Sums two values:
    ...
    ...     >>> add(2, 2)
    ...     FAIL
    ...     """
    ...     return a + b
    >>> class TestAdd(unittest.TestCase):
    ...     def test22(self):
    ...         self.assertEqual(3, add(2, 2))

We can force a test module to return both the doctests and the unittest by
using the ``load_tests()`` method::

    >>> with installed_module('a', to_adopt=[add]),\
    ...         installed_module(
    ...             'ta', to_adopt=[TestAdd],
    ...             code="""
    ...                 from inelegant.finder import TestFinder
    ...                 finder = TestFinder(__name__, 'a')
    ...                 load_tests = finder.load_tests
    ...             """
    ...         ) as ta:
    ...     loader = unittest.TestLoader()
    ...     suite = loader.loadTestsFromModule(ta)
    ...     with open(os.devnull, 'w') as devnull:
    ...         runner = unittest.TextTestRunner(stream=devnull)
    ...         runner.run(suite)
    <unittest.runner.TextTestResult run=2 errors=0 failures=2>

"Inelegant FS" - quick-and-dirty filesystem operations
======================================================

The module ``inelegant.fs`` contains tools to some common file system
operation. Notably, we have some context managers that ensure such operations
are reverted.

Changing working directory
--------------------------

``inelegant.fs.change_dir()`` is a context manager to change directories. While
the context manager is executed, we will be at the given directory; after that,
we will be back to the original one::

    >>> from inelegant.fs import temp_dir, change_dir as cd
    >>> curdir = os.getcwd()
    >>> with temp_dir() as tempdir:
    ...     with cd(tempdir):
    ...         os.getcwd() == curdir
    ...         os.getcwd() == tempdir
    False
    True
    >>> os.getcwd() == curdir
    True

It yields the path to which it moved (which is very practical if one wants
to give an expression to ``change_dir()``)::

    >>> with cd(tempfile.gettempdir()) as path:
    ...     os.getcwd() == path
    True

Creating temporary files
------------------------

``inelegant.fs.temp_file()`` is a context manager that creates temporary
files::

    >>> from inelegant.fs import temp_file
    >>> with temp_file() as p:
    ...     with open(p, 'w') as f:
    ...         _ = f.write('test')
    ...     with open(p, 'r') as f:
    ...         f.read()
    'test'

Once the context is finished, the file is removed::

    >>> open(p, 'r')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    FileNotFoundError: ...

One can also give the path to the file to be created::

    >>> with temp_dir() as tempdir:
    ...     with temp_file(where=tempdir, name='test') as p:
    ...         os.path.basename(p)
    ...         os.path.dirname(p) == tempdir
    ...         os.path.exists(p)
    'test'
    True
    True

If you do not care about the file name but wants it to be created in a
specific directory, you can use the ``where`` argument::

    >>> with temp_file(where=tempfile.gettempdir()) as p:
    ...     os.path.dirname(p) == tempfile.gettempdir()
    ...     os.path.exists(p)
    True
    True

To put some content inside the file, use the ``content`` argument, which can
receive a string::

    >>> with temp_file(content='example') as p:
    ...     with open(p, 'r') as f:
    ...         f.read()
    'example'

Remember, however, that choosing the name, path or directory of the temporary
file can result in errors if one already exists with this name::

    >>> with temp_file(name='example'):
    ...     with temp_file(name='example'): # doctest: +ELLIPSIS
    ...         pass
    Traceback (most recent call last):
      ...
    OSError: ...

Creating temporary directories
------------------------------

``temp_dir()`` is a context manager to create temporary directories. The
yielded value will be the path to the temporary directory::

    >>> with temp_dir() as p:
    ...     os.path.isdir(p)
    True

Once the context is done, the directory is deleted::

    >>> os.path.isdir(p)
    False

To use the temporary directory as the working one, make the ``cd`` argument
true::

    >>> with temp_dir(cd=True) as p:
    ...     os.getcwd() == p
    True

Once the context is closed, we are back to the previous directory::

    >>> curdir = os.getcwd()
    >>> with temp_dir(cd=True) as p:
    ...     os.getcwd() == curdir
    False
    >>> os.getcwd() == curdir
    True

Also, you can choose the directory where to create the new one, as well as its
name::

    >>> with temp_dir() as p1, temp_dir(where=p1) as p2:
    ...     os.path.dirname(p2) == p1
    True
    >>> with temp_dir(name='example') as p:
    ...     os.path.basename(p)
    'example'

Note, however, that choosing the name of the temporary directory can result in
errors if one already exists with this name::

    >>> with temp_dir(name='example'):
    ...     with temp_dir(name='example'): # doctest: +ELLIPSIS
    ...         pass
    Traceback (most recent call last):
      ...
    FileExistsError: ...

"Inelegant Toggle" - enable and disable a global condition
==========================================================

``intelegant.toggle`` is home for the ``Toggle`` class, which generate objects
that can be either disabled or enabled. The main purpose of ``Toggle`` is to
enable global behaviors - most of the time, deprecated behaviors.

A use case
----------

For example, suppose we have a function that returns the quotient of two
numbers. If the divisor is zero, it returns ``float('NaN')``::


    >>> def div(dividend, divisor):
    ...     if divisor != 0:
    ...         return dividend / divisor
    ...     else:
    ...         return float('NaN')
    >>> div(6, 3)
    2.0
    >>> div(6, 0)
    nan

So far, so good. Yet the experience proves that it is not the best choice for
most uses of the function. Developers in general expect the function to raise
an exception for zero divisors. We decide to change this behavor, then::

    >>> def div(dividend, divisor):
    ...     return dividend / divisor
    >>> div(6, 3)
    2.0
    >>> div(6, 0)
    Traceback (most recent call last):
      ...
    ZeroDivisionError: division by zero

The problem is, many programs are already using the function and relying on the
old behavor. To rewrite all of them at once is not viable. We can then enable
the old behavior via toggle, giving the option to the developer to update
later.

First, we create a toggle::

    >>> from inelegant.toggle import Toggle
    >>> div_returns_nan = Toggle()

Then we rewrite the function to use it. To check if the toggle is enabled, we
see its ``enabled`` attribute::

    >>> def div(dividend, divisor):
    ...     try:
    ...         return dividend / divisor
    ...     except ZeroDivisionError:
    ...         if div_returns_nan.enabled:
    ...             return float('NaN')
    ...         else:
    ...             raise

The function will have the new behavior with a disabled toggle (the default
state)::

    >>> div(6, 0)
    Traceback (most recent call last):
      ...
    ZeroDivisionError: division by zero

Once the toggle is enabled, however, the old behavior will emerge::

    >>> div_returns_nan.enable()
    >>> div(6, 0)
    nan

Disabling a toggle
------------------

You can disable a toggle as well::

    >>> div_returns_nan.disable()
    >>> div(6, 0)
    Traceback (most recent call last):
      ...
    ZeroDivisionError: division by zero

This, however, is probably not a good idea most of the time. Currently, toggles
are expected to only be enabled in the very beginning of the Python program and
to stay thsi way for the rest of it. Crucially, toggles are not thread-safe, so
enabling and disabling them at will may result in very strange bugs.

Toggles as context managers
---------------------------

If you are sure there would be no two threads in your program (as we are, since
our tests are executed synchronously), you can use the toggle as a context
manager. During its context, the toggle is enabled; after that, it is
disabled::

    >>> with div_returns_nan:
    ...     div(6, 0)
    nan
    >>> div(6, 0)
    Traceback (most recent call last):
      ...
    ZeroDivisionError: division by zero

A warning for each toogle
-------------------------

Since toggles are used for enabling deprecated behavior, we think it may be a
good idea to always add a warning when it is observed as being enabled. This
way, the developer will be continuously remembered that the program relies in
deprecated behavior::

    >>> def div(dividend, divisor):
    ...     try:
    ...         return dividend / divisor
    ...     except ZeroDivisionError:
    ...         if div_returns_nan.enabled:
    ...             print(
    ...                 'Returning nan for a zero divisor is deprecated '
    ...                 'behavior from div.')
    ...             return float('NaN')
    ...         else:
    ...             raise

    >>> with div_returns_nan:
    ...     div(6, 0)
    Returning nan for a zero divisor is deprecated behavior from div.
    nan

(Also, we would rather write it to ``sys.stderr`` but you got the idea.)

"Inelegant Dict" - dictionaries idioms
======================================

Currently, ``inelegant.dict`` has only one utility, ``temp_key()``. It is a
context manager that adds a key to a dict only during its context. While it is
a very simple context manager, this is a need we see arising time and time
again.

Something like this::

    >>> from inelegant.dict import temp_key
    >>> d = {}
    >>> with temp_key(d, key='a', value=1):
    ...     d
    {'a': 1}

Once the context finishes, the key is gone::

    >>> d
    {}

"Inelegant I/O" - dealing with standard input/output
====================================================

The module ``inelegant.io`` provides tools to control the standard output and
standard error. (It is a bit of a funny name because it does not handle
standard input, right?)

This module has has four utilities. ``redirect_stdout`` and ``redirect_stderr``
are two context managers/decorators that capture output and allow the developer
to see it. ``suppress_stdout`` and ``suppress_stderr`` are similar but only
suppress the output.

Redirecting standard output
---------------------------

``redirect_stdout()`` will redirect the standard output to a file object given
to it::

    >>> from io import StringIO
    >>> from inelegant.io import redirect_stdout
    >>> output = StringIO()
    >>> with redirect_stdout(output):
    ...     print('this will be redirected')

Everything that would get into the standard output will be written to this
file::

    >>> output.getvalue()
    'this will be redirected\n'

Once the context is exited, the previous standard output is restored::

    >>> print('this will not be redirected')
    this will not be redirected

The context manager returns the object to which it will write the redirected
content::

    >>> with redirect_stdout(StringIO()) as o:
    ...     print('new file-like object')
    >>> o.getvalue()
    'new file-like object\n'

If no argument is given to the context manager, it will create and return a
``StringIO`` object::

    >>> with redirect_stdout() as o:
    ...     print('automatically created file-like object')
    >>> o.getvalue()
    'automatically created file-like object\n'

Redirecting standard error
--------------------------

``redirect_stderr()`` will redirect the standard error to a file object given
to it::

    >>> from inelegant.io import redirect_stderr
    >>> output = StringIO()
    >>> with redirect_stderr(output):
    ...     _ = sys.stderr.write('this will be redirected\n')

Everything that would get into the standard output will be written to this
file::

    >>> output.getvalue()
    'this will be redirected\n'

Once the context is exited, the previous standard output is restored::

    >>> _ = sys.stderr.write('this will not be redirected')

The context manager returns the object to which it will write the redirected
content::

    >>> with redirect_stderr(StringIO()) as o:
    ...     _ = sys.stderr.write('new file-like object\n')
    >>> o.getvalue()
    'new file-like object\n'

If no argument is given to the context manager, it will create and return a
``StringIO`` object::

    >>> with redirect_stderr() as o:
    ...     _ = sys.stderr.write('automatically created file-like object\n')
    >>> o.getvalue()
    'automatically created file-like object\n'

Discarding output
-----------------

If you only need to suppress the output of anything that got written into the
standard output, you can use the ``suppress_stdout()`` context manager::

    >>> from inelegant.io import suppress_stdout
    >>> with suppress_stdout():
    ...     print('this will not appear anywhere.')

It also behaves as a decorator if you need. In the example below, the message
written to the standard output is lost::

    >>> @suppress_stdout
    ... def f(a, b):
    ...     print('values of args are', a, b)
    ...     return a+b
    >>> f(1, 2)
    3

``suppress_stderr()`` is very much like ``suppress_stdout()``, with the
difference that it will discard anything written to the standard error
instead::

    >>> from inelegant.io import suppress_stderr
    >>> with redirect_stderr() as output:
    ...     _ = sys.stderr.write('redirected\n')
    ...     with suppress_stderr():
    ...         _ = sys.stderr.write('this will not appear anywhere.')
    ...     _ = sys.stderr.write('redirected, too\n')
    >>> output.getvalue()
    'redirected\nredirected, too\n'

Unsurprisingly, ``suppress_stderr()`` is also a decorator::

    >>> @suppress_stderr
    ... def f(a, b):
    ...     sys.stderr.write('values of args are {0} {1}'.format(a, b))
    ...     return a+b
    >>> with redirect_stderr() as output:
    ...     _ = sys.stderr.write('redirected\n')
    ...     with suppress_stderr():
    ...         f(1, 2)
    ...     _ = sys.stderr.write('redirected, too\n')
    3
    >>> output.getvalue()
    'redirected\nredirected, too\n'

"Inelegant Object" - idioms for objects in general
==================================================

Right now, ``inelegant.object`` contains only ``temp_attr``, a utility function
that replaces the attribute of an object temporarily::

    >>> from inelegant.object import temp_attr

Context manager
---------------

As a context manager, it will replace the attribute during the context. For
example, consider the object ``a`` below::

    >>> class A(object):
    ...     def __init__(self, b):
    ...         self.b = b
    >>> a = A(3)
    >>> a.b
    3

We can use ``temp_attr`` to replace its value for a brief moment::

    >>> with temp_attr(a, attribute='b', value='ok'):
    ...     a.b
    'ok'

Once the context is gone, the previous value is back::

    >>> a.b
    3

Decorator
---------

``temp_attr`` instances also behave as decorators. In this case, the value will
be replaced during the function execution::

    >>> @temp_attr(a, attribute='b', value='ok')
    ... def f():
    ...     global a
    ...     print('The value of "a.b" is {0}.'.format(a.b))
    >>> a.b
    3
    >>> f()
    The value of "a.b" is ok.
    >>> a.b
    3

What happens with non-existent attributes
-----------------------------------------

If there was no such attribute before, then it should not exist after::

    >>> with temp_attr(a, attribute='c', value='ok'):
    ...     a.c
    'ok'
    >>> a.c
    Traceback (most recent call last):
      ...
    AttributeError: 'A' object has no attribute 'c'

Also, this is not supposed to work with objects which do not accept new
attributes to be created:

    >>> with temp_attr(object(), attribute='c', value='fail'):
    ...     pass
    Traceback (most recent call last):
      ...
    AttributeError: 'object' object has no attribute 'c'

Licensing
==============

Inelegant is free software: you can redistribute it and/or modify
it under the terms of the `GNU Lesser General Public License`__ as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

__ http://www.gnu.org/licenses/lgpl-3.0.html

Inelegant is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Inelegant.  If not, see <http://www.gnu.org/licenses/>.

