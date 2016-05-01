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

import multiprocessing
import inspect


class Process(multiprocessing.Process):
    """
    ``Process`` is a ``multiprocessing.Process`` sublclass that starts and
    stops itself automatically::

    >>> import time
    >>> def serve():
    ...     time.sleep(0.001)

    >>> with Process(target=serve) as pc:
    ...     pc.is_alive()
    True
    >>> pc.is_alive()
    False

    Retrieving results and exceptions
    ---------------------------------

    Once the process is finished, the returned value can be retrieved from the
    contextual process::

    >>> def serve():
    ...     return 3

    >>> with Process(target=serve) as pc:
    ...     pass
    >>> pc.result
    3

    It also stores any exception untreated by the spawned process::

    >>> def serve():
    ...     raise Exception('example')

    >>> with Process(target=serve) as pc:
    ...     pass
    >>> pc.exception
    Exception('example',)

    However, it may not be trivial to access the exception attribute in some
    situations where the child process died. In these cases, the ``reraise``
    argument from ``Process`` is handy: it will ensure this very same exception
    is re-raised at the end of the block::

    >>> with Process(target=serve, reraise=True) as pc:
    ...     pass
    Traceback (most recent call last):
      ...
    Exception: example

    Sending and receiving data
    --------------------------

    If the target function is a generator function, then the spawned process
    will block at each ``yield`` statement. The yielded value can be retrieved
    by ``Process.get()``. This method, however, does not make the process
    continue; to do that, one should call ``ProcessContect.go()``:

    >>> def serve():
    ...     yield 1
    ...     yield 2
    ...     yield 5
    >>> with Process(target=serve) as pc:
    ...     pc.get()
    ...     pc.go()
    ...     pc.get()
    ...     pc.go()
    ...     pc.get()
    ...     pc.go()
    1
    2
    5

    >>> def serve():
    ...     value1, value2 = yield 1
    ...     yield (value1+value2)
    >>> with Process(target=serve) as pc:
    ...     value = pc.get()
    ...     pc.send([value, 1])
    ...     sum = pc.get()
    ...     pc.go()
    ...     sum
    2

    Note that ``Process.get()`` will return all values in the order they were
    yielded, even if one call ``Process.send()`` or ``Process.go()`` in the
    meantime::

    >>> def serve():
    ...     yield 1
    ...     yield 2
    ...     yield 5
    >>> with Process(target=serve) as pc:
    ...     pc.go()
    ...     pc.go()
    ...     pc.go()
    ...     pc.get()
    ...     pc.get()
    ...     pc.get()
    1
    2
    5

    Forcing termination
    -------------------

    By default, ``Process`` will be joined to the main process but it is a
    problem if the child process does not end by itself. For example, the
    function below would run forever, blocking the main process at the end of
    the block::

    >>> def forever():
    ...     while True:
    ...         pass

    However, one can set the ``terminate`` argument from ``Process`` to
    ``True``. In this case, the child process will be terminated::

    >>> with Process(target=serve, terminate=True) as pc:
    ...     pc.is_alive()
    True
    >>> pc.is_alive()
    False

    In general, it is better used as a last resort debugging feature: if a
    child process keeps blocking, it can be terminated for easier discovering
    what is going on. However, nothing impedes a user of using it against a
    permanent process (e.g. a server that is ``serve_forever()``).
    """

    def __init__(
            self, group=None, target=None, name=None, args=None, kwargs=None,
            timeout=1, terminate=False, reraise=False,
            daemon=True):
        self.timeout = timeout
        self._terminate = terminate
        self.reraise = reraise

        self.result = None
        self.exception = None

        try:
            self.conversation = Conversation(target)
            self.target = self.conversation.start
        except:
            self.conversation = None
            self.target = target

        self.error_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()

        self.args = args if args is not None else ()
        self.kwargs = kwargs if kwargs is not None else {}
        multiprocessing.Process.__init__(
            self, group=group, target=self.target, name=name
        )

        self.daemon = daemon

    def run(self):
        try:
            result = self.target(*self.args, **self.kwargs)

            self.result_queue.put(result)
            self.error_queue.put(None)
        except Exception as e:
            self.result_queue.put(None)
            self.error_queue.put(e)

    def join(self, timeout=None):
        """
        As the corresponding method from the ``multiprocessing.Process`` class,
        this one will block the execution until the subprocess finishes or the
        timeout is reached. The timeout is optional; if not given, the process
        will block indefinitely.

        A difference from the parent's ``join()`` is that one can retrieve the
        returned value from the target after joining::

        >>> def add(a, b):
        ...     return a+b
        >>> process = Process(target=add, args=(1, 2))
        >>> process.start()
        >>> process.join()
        >>> process.result
        3

        If the target function ends due an untreated exception, it will be
        available as well::

        >>> def fail():
        ...     raise Exception('error')
        >>> process = Process(target=fail)
        >>> process.start()
        >>> process.join()
        >>> process.exception
        Exception('error',)
        """
        multiprocessing.Process.join(self, timeout)

        if not self.error_queue.empty():
            self.exception = self.error_queue.get()
        if not self.result_queue.empty():
            self.result = self.result_queue.get()

        if self.reraise and self.exception is not None:
            raise self.exception

    def get(self):
        """
        Retrieves a value yielded by the target function::

        >>> def serve():
        ...     yield 1
        >>> with Process(target=serve) as pc:
        ...     value = pc.get()
        ...     pc.go()
        ...     value
        1

        It fails if the ``Process`` target is not a generator
        function::

        >>> import time
        >>> def cannot_send_anything():
        ...     time.sleep(0.001)
        >>> with Process(target=cannot_send_anything) as pc:
        ...     value = pc.get()
        Traceback (most recent call last):
          ...
        ValueError: cannot_send_anything is not a generator function and so ca\
nnot send values back before returning.
        """
        if self.conversation is None:
            raise ValueError(
                '{0} is not a generator function and so cannot send values '
                'back before returning.'.format(self.target.__name__)
            )

        return self.conversation.get_from_child()

    def send(self, value):
        """
        Sends a value to be returned by the ``yield`` statement at the target
        function::

        >>> def serve():
        ...     value = yield
        ...     yield value + 1
        >>> with Process(target=serve) as pc:
        ...     pc.send(1)
        ...     pc.get() # Ignored, from the first yield.
        ...     value = pc.get()
        ...     pc.go()
        ...     value
        2


        It fails if the ``Process`` target is not a generator
        function::

        >>> import time
        >>> def cannot_receive_anything():
        ...     time.sleep(0.001)
        >>> with Process(target=cannot_receive_anything) as pc:
        ...     value = pc.send(1)
        Traceback (most recent call last):
          ...
        ValueError: cannot_receive_anything is not a generator function and so\
 cannot receive values after starting up.
        """
        if self.conversation is None:
            raise ValueError(
                '{0} is not a generator function and so cannot receive values '
                'after starting up.'.format(self.target.__name__)
            )

        self.conversation.send_to_child(value)

    def go(self):
        """
        Makes a process blocked by a ``yield`` statement proceed with its
        execution. It is equivalent to ``Process.send(None)``.

        It fails if the ``Process`` target is not a generator
        function::

        >>> import time
        >>> def cannot_go():
        ...     time.sleep(0.001)
        >>> with Process(target=cannot_go) as pc:
        ...     value = pc.go()
        Traceback (most recent call last):
          ...
        ValueError: cannot_go is not a generator function. It cannot be stoppe\
d - much less go ahead after stopping.
        """
        if self.conversation is None:
            raise ValueError(
                '{0} is not a generator function. It cannot be stopped - much '
                'less go ahead after stopping.'.format(self.target.__name__)
            )

        self.conversation.send_to_child(None)

    def __enter__(self):
        self.start()

        return self

    def __exit__(self, type, value, traceback):
        if value is not None or self._terminate:
            self.terminate()

        self.join(self.timeout)


class Conversation(object):
    """
    ```Conversation``` provides a somewhat more succinct way to interact with a
    function running in a different process.

    Creating a conversation
    -----------------------

    ``Conversation`` receives a generator function as its argument; giving a
    normal function will result in error. Once created, the bound ``start()``
    method from the conversation can be given as a target to
    ``multiprocessing.Process``. So, we could have a function like this::

    >>> def f():
    ...     value = yield 1
    ...     yield value + 1

    ...that would be used like this::

    >>> conversation = Conversation(function=f)
    >>> import multiprocessing
    >>> process = multiprocessing.Process(target=conversation.start)
    >>> process.start()

    "Talking" and "listening" to the process
    ----------------------------------------

    Once a conversation process started, there should follow a series of steps
    where, for each ``yield`` in the generator function, the main process first
    gets the yielded value and then send a value back::

    >>> conversation.get_from_child()
    1
    >>> conversation.send_to_child(2)
    >>> conversation.get_from_child()
    3
    >>> conversation.send_to_child(None)
    >>> process.join()

    **It is mandatory to always get and send a value to each ``yield``
    statement.** You may note that we send a ``None`` value to the child
    process before joining the process. If we do not do that, the joined
    process will be blocked - and the main process as well.
    """
    def __init__(self, function):
        if not inspect.isgeneratorfunction(function):
            raise TypeError('Conversations require generator functions.')

        self.function = function
        self.child_to_parent = multiprocessing.Queue()
        self.parent_to_child = multiprocessing.Queue()

    def start(self, *args, **kwargs):
        generator = self.function(*args, **kwargs)
        try:
            self.converse(generator)
        except Exception as e:
            generator.throw(e)

    def get_from_child(self):
        return self.child_to_parent.get()

    def send_to_child(self, value):
        self.parent_to_child.put(value)

    def converse(self, generator):
        to_parent = generator.next()
        while True:
            try:
                self.child_to_parent.put(to_parent)
                from_parent = self.parent_to_child.get()
                to_parent = generator.send(from_parent)
            except StopIteration:
                break
