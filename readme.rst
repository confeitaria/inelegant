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
