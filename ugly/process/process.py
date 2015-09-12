import multiprocessing
import inspect

class ProcessContext(object):
    """
    ``ProcessContext`` starts and stops a ``multiprocessing.Process`` instance
    automatically::

    >>> def serve():
    ...     time.sleep(0.001)

    >>> with ProcessContext(target=serve) as pc:
    ...     pc.process.is_alive()
    True
    >>> pc.process.is_alive()
    False

    Retrieving exceptions
    ---------------------

    It also stores any exception untreated by the spawned process::

    >>> def serve():
    ...     raise Exception('example')

    >>> with ProcessContext(target=serve) as pc:
    ...     pass
    >>> pc.exception
    Exception('example',)

    Sending and receiving data
    --------------------------

    If the target function is a generator function, then the spawned process
    will block at each ``yield`` statement. The yielded value can be retrieved
    by ``ProcessContect.get()``. This method, however, does not make the process
    continue; to do that, one should call ``ProcessContect.go()``:

    >>> def serve():
    ...     yield 1
    ...     yield 2
    ...     yield 5
    >>> with ProcessContext(target=serve) as pc:
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
    >>> with ProcessContext(target=serve) as pc:
    ...     value = pc.get()
    ...     pc.send([value, 1])
    ...     sum = pc.get()
    ...     pc.go()
    ...     sum
    2

    Note that ``ProcessContect.get()`` will return all values in the order they
    were yielded, even if one call ``ProcessContect.send()`` or
    ``ProcessContect.go()`` in the meantime::

    >>> def serve():
    ...     yield 1
    ...     yield 2
    ...     yield 5
    >>> with ProcessContext(target=serve) as pc:
    ...     pc.go()
    ...     pc.go()
    ...     pc.go()
    ...     pc.get()
    ...     pc.get()
    ...     pc.get()
    1
    2
    5
    """

    def __init__(self, target, args=(), timeout=1):
        self.timeout = timeout
        self.exception = None
        self.conversation = Conversation(target)
        self.process = multiprocessing.Process(
            target=self.conversation.start, args=args
        )

    def get(self):
        """
        Retrieves a value yielded by the target function::

        >>> def serve():
        ...     yield 1
        >>> with ProcessContext(target=serve) as pc:
        ...     value = pc.get()
        ...     pc.go()
        ...     value
        1
        """
        return self.conversation.get_from_child()

    def send(self, value):
        """
        Sends a value to be returned by the ``yield`` statement at the target
        function::

        >>> def serve():
        ...     value = yield
        ...     yield value + 1
        >>> with ProcessContext(target=serve) as pc:
        ...     pc.send(1)
        ...     pc.get() # Ignored, from the first yield.
        ...     value = pc.get()
        ...     pc.go()
        ...     value
        2
        """
        self.conversation.send_to_child(value)

    def go(self):
        """
        Makes a process blocked by a ``yield`` statement proceed with its
        execution. It is equivalent to ``ProcessContect.send(None)``.
        """
        self.conversation.send_to_child(None)

    def __enter__(self):
        self.process.start()
        return self

    def __exit__(self, type, value, traceback):
        if value is not None:
            self.process.terminate()

        self.process.join(self.timeout)
        self.exception = self.conversation.get_error()
        self.result = self.conversation.get_result()

class Conversation(object):

    def __init__(self, function):
        self.function = function
        self.child_to_parent = multiprocessing.Queue()
        self.parent_to_child = multiprocessing.Queue()
        self.error = multiprocessing.Queue()
        self.result = multiprocessing.Queue()

    def start(self, *args, **kwargs):
        try:
            value = self.function(*args, **kwargs)

            if inspect.isgeneratorfunction(self.function):
                self.converse(value)
            else:
                self.result.put(value)
        except Exception as e:
            self.error.put(e)

    def get_from_child(self):
        return self.child_to_parent.get()

    def send_to_child(self, value):
        self.parent_to_child.put(value)

    def get_error(self):
        if not self.error.empty():
            return self.error.get()

    def get_result(self):
        if not self.result.empty():
            return self.result.get()

    def converse(self, generator):
        to_parent = generator.next()
        while True:
            try:
                self.child_to_parent.put(to_parent)
                from_parent = self.parent_to_child.get()
                to_parent = generator.send(from_parent)
            except StopIteration:
                break
