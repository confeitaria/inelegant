import multiprocessing

class ProcessContext(object):

    def __init__(self, target, args=(), timeout=1):
        self.timeout = timeout
        self.process = multiprocessing.Process(target=target, args=args)

    def __enter__(self):
        self.process.start()
        return self

    def __exit__(self, type, value, traceback):
        self.process.join(self.timeout)
