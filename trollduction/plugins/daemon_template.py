"""Template for trollflow daemons showing the necessary parts. Rename
everything having 'Template' in the name, and also rename 'Worker'
class."""

import logging
import Queue
from threading import Thread
import time

class TemplateContainer(object):

    """Thread container for Worker instance"""

    logger = logging.getLogger("TemplateContainer")

    def __init__(self):
        self.worker = None
        self._input_queue = None
        self.output_queue = Queue.Queue()
        self.thread = None

        # Create a worker instance
        self.worker = Worker()

        # Start the Worker into a new daemonized thread.
        self.thread = Thread(target=self.worker.run)
        self.thread.setDaemon(True)
        self.thread.start()

    @property
    def input_queue(self):
        """Input queue property"""
        return self._input_queue

    @input_queue.setter
    def input_queue(self, queue):
        """Setter for input queue property"""
        self._input_queue = queue
        self.gatherer.queue = queue

    def __setstate__(self, state):
        self.__init__(**state)

    def stop(self):
        """Stop gatherer."""
        self.logger.debug("Stopping Worker.")
        self.gatherer.stop()
        self.thread.join()
        self.logger.debug("Worker stopped.")
        self.thread = None

class Worker(Thread):

    """Template for a threaded worker."""

    logger = logging.getLogger("Worker")

    def __init__(self, arg1, arg2=None):
        Thread.__init__(self)
        self.queue = queue
        self._loop = False
        self.arg1 = arg1
        self.arg2 = arg2

    def run(self):
        """Run the worker"""
        self._loop = True
        while self._loop:
            if self.queue is not None:
                try:
                    data = self.queue.get(True, 1)
                except Queue.Empty:
                    continue
                self.logger.info("New data received.")
                res = do_stuff(data)
            else:
                time.sleep(1)

    def stop(self):
        """Stop Worker"""
        self._loop = False

    @property
    def loop(self):
        """Loop property"""
        return self._loop
