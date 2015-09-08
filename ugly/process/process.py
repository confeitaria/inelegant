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
        self.from_process_queue = multiprocessing.Queue()
        self.to_process_queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(
            target=self._conversational(target), args=args
        )

    def get(self):
        return self.from_process_queue.get()

    def send(self, value):
        self.to_process_queue.put(value)

    def go(self):
        self.send(None)

    def __enter__(self):
        self.process.start()
        return self

    def __exit__(self, type, value, traceback):
        if value is not None:
            self.process.terminate()

        self.process.join(self.timeout)
        while not self.exceptions_queue.empty():
            self.exceptions.append(self.exceptions_queue.get())

    def _conversational(self, target):
        def f(*args, **kwargs):
            try:
                value = target(*args, **kwargs)
                if inspect.isgeneratorfunction(target):
                    self._converse(value)
            except Exception as e:
                self.exceptions_queue.put(e)

        return f

    def _converse(self, generator):
        generated_value = generator.next()
        while True:
            try:
                self.from_process_queue.put(generated_value)
                sent_value = self.to_process_queue.get()
                generated_value = generator.send(sent_value)
            except StopIteration:
                break
