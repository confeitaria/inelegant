import multiprocessing

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

    It also stores any exception raised by the spawned process::

    >>> def serve():
    ...     raise Exception('example')

    >>> with ProcessContext(target=serve) as pc:
    ...     pass
    >>> pc.exceptions
    [Exception('example',)]
    """

    def __init__(self, target, args=(), timeout=1):
        self.timeout = timeout
        self.exceptions = []
        self.exceptions_queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(
            target=self.queue_exception(target), args=args
        )

    def __enter__(self):
        self.process.start()
        return self

    def __exit__(self, type, value, traceback):
        if value is not None:
            self.process.terminate()

        self.process.join(self.timeout)
        while not self.exceptions_queue.empty():
            self.exceptions.append(self.exceptions_queue.get())

    def queue_exception(self, target):
        def f(*args, **kwargs):
            try:
                target(*args, **kwargs)
            except Exception as e:
                self.exceptions_queue.put(e)

        return f
