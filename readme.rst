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

Right now there are four modules in this project.

"Inelegant Process" - running and communicating with a simple processes
=======================================================================

This module contains the class ``inprocess.Process``. This class extends
``multiprocessing.Process`` so one can easily recover information sent
by the target.

Returned values and exceptions
------------------------------

For example, one can get the returned value::

    >>> import inelegant.process as inprocess
    >>> def invert(n):
    ...     return 1.0/n
    >>> process = inprocess.Process(target=invert, args=(2.0,))
    >>> process.start()
    >>> process.join() # The value is only available after the process end.
    >>> process.result
    0.5

If the process is finished by an exception, it can also be retrieved::

    >>> process = inprocess.Process(target=invert, args=(0.0,))
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
    >>> process = inprocess.Process(target=add)
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

A very nice feature of ``inprocess.Process`` is that it is a context
manager. If one is given to a ``with`` statement, it is guaranteed that it will
be finished after the block ends. This is useful because it is too easy to
forget to join a process. If it happens, we have problems::

    >>> process = inprocess.Process(target=invert, args=(4,))
    >>> process.start()
    >>> process.result + 3 # Oops, the value is not available yet!
    Traceback (most recent call last):
      ...
    TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
    >>> process.join() # Alas, it is too late.

Using the ``with`` statement it is done automatically and without way less
clutter. The process starts itself before proceeding and is joined once the
block ends. The parent process will wait for its child's end after the block::

    >>> with inprocess.Process(target=invert, args=(4,)) as process:
    ...     pass
    >>> process.result
    0.25

    >>> process = inprocess.Process(target=invert, args=(0.0,))
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
    >>> with inprocess.Process(target=forever, terminate=True) as process:
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

    >>> process = inprocess.Process(target=invert, args=(0.0,), reraise=True)
    >>> process.start()
    >>> process.join()
    Traceback (most recent call last):
      ...
    ZeroDivisionError: float division by zero

Since the process is joined after the block if given to a ``with`` statement,
children exceptions would also be raised - but only after the block finishes::

    >>> with inprocess.Process(target=invert, args=(0.0,), reraise=True):
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

For example, it has the ``innet.Server``, a subclass of
``SocketServer.TCPServer`` that only serves a string in a specific port::

    >>> import inelegant.net as innet
    >>> server = innet.Server('localhost', 9000, message='my message')
    >>> import contextlib, socket, time
    >>> with inprocess.Process(target=server.handle_request):
    ...     time.sleep(0.1)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         s.connect(('localhost', 9000))
    ...         s.recv(10)
    'my message'

However, it is probably best used as a context manager. If given to a ``with``
statement, the server will be started alone in the background and finished once
the block is exited::

    >>> with innet.Server('localhost', 9000, message='my message'):
    ...     time.sleep(0.1)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         s.connect(('localhost', 9000))
    ...         s.recv(10)
    'my message'
    >>> with contextlib.closing(socket.socket()) as s:
    ...     s.connect(('localhost', 9000))
    Traceback (most recent call last):
      ...
    error: [Errno 111] Connection refused

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

        >>> with innet.Server('localhost', 9000, message='my message'):
        ...     time.sleep(0.01)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         s.connect(('localhost', 9000))
        ...         s.recv(10)
        'my message'

    The problem is, these wait times are wasteful: to ensure the server is up,
    we wait way more time than it is necessary most of the times. It is
    unreliable, too, because there will be always a time when the waiting time
    is not enough.

    With ``wait_server_up()``, the process waits only for the necessary amount
    of time - and no more::

        >>> start = time.time()
        >>> with innet.Server('localhost', 9000, message='my message'):
        ...     innet.wait_server_up('localhost', 9000)
        ...     time.time() - start < 0.01
        True

    It has a timeout: by default, it will not wait more than one second and, if
    the server is not up, an exception is raised. It can be made longer with the
    ``timeout`` argument::

        >>> start = time.time()
        >>> with innet.Server('localhost', 9000):
        ...     innet.wait_server_up('localhost', 9000, timeout=60)
        ...     time.time() - start < 0.01
        True


``wait_server_down()``
    Likewise, it is common to have to wait for a server being down on a specific
    port. Again, it is common to rely on waiting times. Consider the hypotetical
    server below::

        >>> def slow_server():
        ...     with innet.Server('localhost', 9000) as server:
        ...         yield
        ...         time.sleep(0.01)
        ...         server.shutdown()

    If we start and shutdown it, and then try to bound to the same port, it will
    likely fail::

        >>> with inprocess.Process(target=slow_server) as p:
        ...     innet.wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         s.bind(('localhost', 9000))
        Traceback (most recent call last):
         ...
        error: [Errno 98] Address already in use

    A common solution is to add some wait time::

        >>> with inprocess.Process(target=slow_server) as p:
        ...     innet.wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         time.sleep(0.02)
        ...         s.bind(('localhost', 9000))

    Again, it is a suboptimal. Generally, the wait time is way larger
    than needed most of the time, and even in this situation it will fail
    sometimes.. With ``wait_server_down()``, the client can block itself until
    the server is not running anymore - and no more::

        >>> with inprocess.Process(target=slow_server) as p:
        ...     innet.wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         innet.wait_server_down('localhost', 9000)
        ...         s.bind(('localhost', 9000))

    It will wait for at most one second by default, but the timeout can be
    changed::

        >>> with inprocess.Process(target=slow_server) as p:
        ...     innet.wait_server_up('localhost', 9000)
        ...     with contextlib.closing(socket.socket()) as s:
        ...         p.go() # Request shutdown
        ...         innet.wait_server_down('localhost', 9000, timeout=60)
        ...         s.bind(('localhost', 9000))

"Inelegant Module" - creating modules
=====================================

With ``inelegant.module`` one can create and import modules at runtime, without
needing to write a file.

The ``create_module()`` function
--------------------------------

To create a module, one can use the ``create_module()`` function. The function
has a mandatory argument, the module name::

    >>> import inelegant.module as inmodule
    >>> inmodule.create_module('m') # doctest: +ELLIPSIS
    <module 'm' ...>

A nice thing about ``create_module()`` is that the module will be available to
be imported once it is created::

    >>> import m
    >>> m # doctest: +ELLIPSIS
    <module 'm' ...>

Giving scope, definitions and code to the module
------------------------------------------------

An empty module is not very useful, so ``create_module()`` provides some ways
of putting stuff on it. She simplest one is probably the ``scope`` argument. It
should be a dictionary, and every value from it will be attributed to a variable
whose name is its key::

    >>> m = inmodule.create_module('m', scope={'x': 3})
    >>> m.x
    3

Modules can also define classes and functions. Such entities, when defined on a
module, will have a ``__module__`` attribute set. If one passes these entities
through the scopes dict, however, the module name will not have it set::

    >>> class Class(object):
    ...     pass
    >>> m = inmodule.create_module('m', scope={'Class': Class})
    >>> m.Class.__module__ == 'm'
    False

 One should pass them through the ``defs`` argument (which should be iterable)
 to have the classes and functions "adopted" by the module::

    >>> m = inmodule.create_module('m', defs=[Class])
    >>> m.Class.__module__
    'm'

Finally, sometimes it is more practical to just pass a bunch of code to be
executed as the module source. In these cases, the ``code`` attribute should be
used::

    >>> m = inmodule.create_module('m', scope={'x': 3}, code="""
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

While it is practical to have the module available for importing once it is
created, it may lead to confusio in tests. If many modules are created, it is
feasible that some names may be repeated. To avoid any issue, we can use the
``installed_module()`` functions. It receives exactly the same arguments from
``create_module()`` but returns a context manager. If given to a ``with``
statement, the module will be available for importing...

::

    >>> with inmodule.installed_module('some_module', scope={'x': 3}) as m:
    ...     import some_module
    ...     m == some_module
    True

...but only inside the ``with`` block::

    >>> import some_module
    Traceback (most recent call last):
      ...
    ImportError: No module named some_module

The ``get_caller_module()`` function
------------------------------------

Finally, ``inelegant.module`` provides the ``get_caller_module()`` function. It
basically returns the module from where the current function was called.

For example, suppose we have a module ``m1`` with a function ``f()``::

    >>> def f():
    ...     print inmodule.get_caller_module()

``m2`` imports ``m1`` and call it. What will it return? It will return ``m2``
since it is the module calling ``f()``::

    >>> with inmodule.installed_module('m1', defs=[f]),\
    ...         inmodule.installed_module('m2', code='import m1; m1.f()'):
    ...     pass # doctest: +ELLIPSIS
    <module 'm2' ...>

As we like to put it, ``get_caller_module()`` doesn't tell you who you are - you
already know that. I tell you who is calling you.

That said, ``get_caller_module()`` accepts an index as its argument. In this
case, it will return the n-th module from the frame stack, being 0 the module
where ``get_caller_module()`` was called. Basically, it means the default value
of the index is 1::

    >>> def f2():
    ...     print inmodule.get_caller_module(1)
    >>> with inmodule.installed_module('m1', defs=[f2]),\
    ...         inmodule.installed_module('m2', code='import m1; m1.f2()'):
    ...     pass # doctest: +ELLIPSIS
    <module 'm2' ...>

"Inelegant Finder": straightforward way of finding test cases
=============================================================

Finally, we have ``infinder.TestFinder``, a ``unittest.TestSuite``
subclass that finds tests by itself.

Finding tests in modules
------------------------

``infinder.TestFinder`` can receive an arbitrary number of modules as
its constructor arguments. The finder will then find every test case from these
modules, as well as any doctests in docstrings from it.

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
    ...         self.assertEquals(3, add(2, 2))

We can put them on modules and give the modules to test finder. Both the
doctest and the unit test will be called when the finder suite be executed::

    >>> import inelegant.finder as infinder
    >>> with inmodule.installed_module('a', defs=[add]) as a,\
    ...         inmodule.installed_module('ta', defs=[TestAdd]) as ta:
    ...     finder = infinder.TestFinder(a, ta)
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

    >>> with inmodule.installed_module('a', defs=[add]),\
    ...         inmodule.installed_module('ta', defs=[TestAdd]):
    ...     finder = infinder.TestFinder('a', 'ta')
    ...     import os
    ...     runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    ...     runner.run(finder) # doctest: +ELLIPSIS
    <unittest.runner.TextTestResult run=2 errors=0 failures=2>

Loading doctests in files
-------------------------

The ``infinder.TestFinder`` also accepts file paths (or even file
objects) as its arguments. In this case, the file is expected to be a text file
containing doctests (like yours truly, indeed).

Another good example would be the file created below::

    >>> import tempfile
    >>> _, path = tempfile.mkstemp()
    >>> with open(path, 'w') as f:
    ...     f.write('''
    ...         >>> 2+2
    ...         3
    ...     ''')

We just need to give the path to the finder::

    >>> finder = infinder.TestFinder(path)
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

The file path can be either relative or absolute. If it is not absolute, it will
be relative to the module where ``infinder.TestFinder`` was
instantiated.

The ``load_tests()`` method
---------------------------

Python's ``unittest`` has this nice feature named "`load_tests protocol`__". To
understand it, one should know that ``TestLoader.loadTestsFromModule()`` looks
for all subclasses of ``unittest.TestCase`` inside the modules given to it:

__ https://docs.python.org/2/library/unittest.html#load-tests-protocol

::

    >>> class TestCase1(unittest.TestCase):
    ...     def test1(self):
    ...         self.assertEquals(1, 1)
    >>> class TestCase2(unittest.TestCase):
    ...     def test2(self):
    ...         self.assertEquals(2, 1)
    >>> with inmodule.installed_module('t', defs=[TestCase1,TestCase2]) as t:
    ...     loader = unittest.TestLoader()
    ...     suite = loader.loadTestsFromModule(t)
    ...     runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    ...     runner.run(suite)
    <unittest.runner.TextTestResult run=2 errors=0 failures=1>

We can change this default behavior by defining a function called
``load_tests()`` in the module. This function receives three arguments: an
``unittest.TestLoader`` instance, a test suite with all tests found in the
module, and a pattern to match files (only really useful when loading tests
from packages). ``load_tests()`` should itself return a test suite - and this
test suite will be the one returned by ``loadTestsFromModule()``. With this, one
can customize which tests are loaded from the module. For example, the code
below will only run ``TestCase1``, although there are two test cases in the
module::

    >>> def load_tests(loader, tests, pattern):
    ...     # We merely ignore the given tests.
    ...     suite = unittest.TestSuite()
    ...     suite.addTest(loader.loadTestsFromTestCase(TestCase1))
    ...     return suite
    >>> with inmodule.installed_module(
    ...         't', defs=[TestCase1, TestCase2, load_tests]
    ...     ) as t:
    ...     loader = unittest.TestLoader()
    ...     suite = loader.loadTestsFromModule(t)
    ...     runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    ...     runner.run(suite)
    <unittest.runner.TextTestResult run=1 errors=0 failures=0>

For its turn, ``infinder.TestFinder`` has a method called
``load_tests()`` that merely returns the finder instance itself - also, it
accepts the three expected arguments. So, if you want the automatic test
discoverers (such as ``unittest.TestLoader.loadTestsFromModule()``) to load all
tests found by ``TestFinder`` in a module, you just need to assign the
instance's ``load_tests()`` method to the ``load_tests`` module variable.

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
    ...         self.assertEquals(3, add(2, 2))

We can force a test module to return both the doctests and the unittest by using
the ``load_tests()`` method::

    >>> with inmodule.installed_module('a', defs=[add]),\
    ...         inmodule.installed_module(
    ...             'ta', defs=[TestAdd],
    ...             code="""
    ...                 import inelegant.finder as infinder
    ...                 finder = infinder.TestFinder(__name__, 'a')
    ...                 load_tests = finder.load_tests
    ...             """
    ...         ) as ta:
    ...     loader = unittest.TestLoader()
    ...     suite = loader.loadTestsFromModule(ta)
    ...     runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    ...     runner.run(suite)
    <unittest.runner.TextTestResult run=2 errors=0 failures=2>

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

