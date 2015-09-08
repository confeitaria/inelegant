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

    It also stores any exception untreated by the spawned process::

    >>> def serve():
    ...     raise Exception('example')

    >>> with ProcessContext(target=serve) as pc:
    ...     pass
    >>> pc.exception
    Exception('example',)
    """

    def __init__(self, target, args=(), timeout=1):
        self.timeout = timeout
        self.exception = None
        self.conversation = Conversation(target)
        self.process = multiprocessing.Process(
            target=self.conversation, args=args
        )

    def get(self):
        return self.conversation.talk()

    def send(self, value):
        self.conversation.listen(value)

    def go(self):
        self.conversation.listen(None)

    def __enter__(self):
        self.process.start()
        return self

    def __exit__(self, type, value, traceback):
        if value is not None:
            self.process.terminate()

        self.process.join(self.timeout)
        self.exception = self.conversation.get_error()

class Conversation(object):

    def __init__(self, function):
        self.listen_from = multiprocessing.Queue()
        self.talk_to = multiprocessing.Queue()
        self.errors_to = multiprocessing.Queue()
        self.function = function

    def __call__(self, *args, **kwargs):
        f = self.start_conversation(self.function)
        return f(*args, **kwargs)

    def talk(self):
        return self.talk_to.get()

    def listen(self, value):
        self.listen_from.put(value)

    def get_error(self):
        if not self.errors_to.empty():
            return self.errors_to.get()

    def start_conversation(self, function):
        def f(*args, **kwargs):
            try:
                value = function(*args, **kwargs)

                if inspect.isgeneratorfunction(function):
                    self.converse(value)
            except Exception as e:
                self.errors_to.put(e)

        return f

    def converse(self, generator):
        to_talk = generator.next()
        while True:
            try:
                self.talk_to.put(to_talk)
                listened = self.listen_from.get()
                to_talk = generator.send(listened)
            except StopIteration:
                break
