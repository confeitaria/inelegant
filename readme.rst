============================================
Ugly, a directory of weird helpers for tests
============================================

or

=======================================
Ugly, rather inelegant than unavailable
=======================================

Ugly groups a series of tools that are very useful for automating tests. Most of
them are unreliable or costly "in the wild" (while they may be unusually
reliable and efficient on tests).

Right now there are four modules in this project.

"Ugly Process": running and communicating with a simple processes
=================================================================

This module contains the class ``ugly.process.Process``. This class extends
``multiprocessing.Process`` so one can easily recover information sent
by the target.

Returned values and exceptions
------------------------------

For example, one can get the returned value::

    >>> import ugly.process
    >>> def invert(n):
    ...     return 1.0/n
    >>> process = ugly.process.Process(target=invert, args=(2.0,))
    >>> process.start()
    >>> process.join() # The value is only available after the process end.
    >>> process.result
    0.5

If the process is finished by an exception, it can also be retrieved::

    >>> process = ugly.process.Process(target=invert, args=(0.0,))
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
    >>> process = ugly.process.Process(target=add)
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

A very nice feature of ``ugly.process.Process`` is that it is a context manager.
If one is given to a ``with`` statement, it is guaranteed that it will be
finished after the block ends. This is useful because it is too easy to forget
to join a process. If it happens, we have problems::

    >>> process = ugly.process.Process(target=invert, args=(4,))
    >>> process.start()
    >>> process.result + 3 # Oops, the value is not available yet!
    Traceback (most recent call last):
      ...
    TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
    >>> process.join() # Alas, it is too late.

Using the ``with`` statement it is done automatically and without way less
clutter. The process starts itself before proceeding and is joined once the
block ends. The parent process will wait for its child's end after the block::

    >>> with ugly.process.Process(target=invert, args=(4,)) as process:
    ...     pass
    >>> process.result
    0.25

    >>> process = ugly.process.Process(target=invert, args=(0.0,))
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
    >>> with ugly.process.Process(target=forever, terminate=True) as process:
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

    >>> process = ugly.process.Process(target=invert, args=(0.0,), reraise=True)
    >>> process.start()
    >>> process.join()
    Traceback (most recent call last):
      ...
    ZeroDivisionError: float division by zero

Since the process is joined after the block if given to a ``with`` statement,
children exceptions would also be raised - but only after the block finishes::

    >>> with ugly.process.Process(target=invert, args=(0.0,), reraise=True):
    ...     executed = True
    Traceback (most recent call last):
      ...
    ZeroDivisionError: float division by zero
    >>> executed
    True

"Ugly Net": quick and dirty network tricks
==========================================

The module ``ugly.net`` provides tools for easing testing some very simple
network communication code.

The ``Server`` class
--------------------

For example, it has the ``ugly.net.Server``, a
subclass of ``SocketServer.TCPServer`` that only serves a string in a specific
port::

    >>> import ugly.net
    >>> server = ugly.net.Server('localhost', 9000, message='my message')
    >>> import contextlib, socket, time
    >>> with ugly.process.Process(target=server.handle_request):
    ...     time.sleep(0.01)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         s.connect(('localhost', 9000))
    ...         s.recv(10)
    'my message'

However, it is probably best used as a context manager. If given to a ``with``
statement, the server will be started alone in the background and finished once
the block is exited::

    >>> with ugly.net.Server('localhost', 9000, message='my message'):
    ...     time.sleep(0.01)
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

To be honest, the ``Server`` class is mostly used to test the reason of the Ugly
Net: the waiter functions.

These functions wait for a port to be up or down in a specific host. There are
two of them:

``wait_server_up(host, port)``
    Blocks until there is a process listening at the given port from the given
    host. Useful when we want to do something only when a server is already up
    and running.

    It is not uncommon a server can take a bit of time to start due to resource
    loading etc. For example, consider the example we saw below. If we remove
    the waiting time from the second line, it will probably fail::

    >>> with ugly.net.Server('localhost', 9000, message='my message'):
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
    >>> with ugly.net.Server('localhost', 9000, message='my message'):
    ...     ugly.net.wait_server_up('localhost', 9000)
    ...     time.time() - start < 0.01
    True

    It has a timeout: by default, it will not wait more than one second and, if
    the server is not up, an exception is raised. It can be made longer with the
    ``timeout`` argument::

    >>> start = time.time()
    >>> with ugly.net.Server('localhost', 9000):
    ...     ugly.net.wait_server_up('localhost', 9000, timeout=60)
    ...     time.time() - start < 0.01
    True


``wait_server_down()``
    Likewise, it is common to have to wait for a server being down on a specific
    port. Again, it is common to rely on waiting times. Consider the hypotetical
    server below::

    >>> def slow_server():
    ...     with ugly.net.Server('localhost', 9000) as server:
    ...         yield
    ...         time.sleep(0.01)
    ...         server.shutdown()

    If we start and shutdown it, and then try to bound to the same port, it will
    likely fail::

    >>> with ugly.process.Process(target=slow_server) as p:
    ...     ugly.net.wait_server_up('localhost', 9000)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         p.go() # Request shutdown
    ...         s.bind(('localhost', 9000))
    Traceback (most recent call last):
     ...
    error: [Errno 98] Address already in use

    A common solution is to add some wait time::

    >>> with ugly.process.Process(target=slow_server) as p:
    ...     ugly.net.wait_server_up('localhost', 9000)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         p.go() # Request shutdown
    ...         time.sleep(0.02)
    ...         s.bind(('localhost', 9000))

    Again, it is a suboptimal. Generally, the wait time is way larger
    than needed most of the time, and even in this situation it will fail
    sometimes.. With ``wait_server_down()``, the client can block itself until
    the server is not running anymore - and no more::

    >>> with ugly.process.Process(target=slow_server) as p:
    ...     ugly.net.wait_server_up('localhost', 9000)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         p.go() # Request shutdown
    ...         ugly.net.wait_server_down('localhost', 9000)
    ...         s.bind(('localhost', 9000))

    It will wait for at most one second by default, but the timeout can be
    changed::

    >>> with ugly.process.Process(target=slow_server) as p:
    ...     ugly.net.wait_server_up('localhost', 9000)
    ...     with contextlib.closing(socket.socket()) as s:
    ...         p.go() # Request shutdown
    ...         ugly.net.wait_server_down('localhost', 9000, timeout=60)
    ...         s.bind(('localhost', 9000))
