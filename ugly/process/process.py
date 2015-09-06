import multiprocessing

class ProcessContext(object):

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
