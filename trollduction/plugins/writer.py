
import Queue
from threading import Thread
import logging
import time

LOGGER = logging.getLogger("DataWriter")

class DataWriterContainer(object):

    '''Container for listener instance
    '''

    def __init__(self, topics=None):
        self.listener = None
        self.input_queue = None
        self.output_queue = Queue.Queue()
        self.thread = None

        # Create a Writer instance
        self.writer = DataWriter(queue=self.input_queue)
        # Start Listener instance into a new daemonized thread.
        self.thread = Thread(target=self.writer.run)
        self.thread.setDaemon(True)
        self.thread.start()

    @property
    def writer(self):
        return self.writer

    @writer.setter
    def writer(self, queue):
        self.writer.queue = queue

    def __setstate__(self, state):
        self.__init__(**state)

#    def __

    def restart_listener(self, topics):
        '''Restart listener after configuration update.
        '''
        if self.listener is not None:
            if self.listener.running:
                self.stop()
        self.__init__(topics=topics)

    def stop(self):
        '''Stop writer.'''
        LOGGER.debug("Stopping writer.")
        self.writer.stop()
        self.thread.join()
        self.thread = None
        LOGGER.debug("Writer stopped.")

class DataWriter(Thread):
    """Writes data to disk.
    """

    def __init__(self, queue=None):
        Thread.__init__(self)
        self.queue = queue
        self._loop = False

    def run(self):
        """Run the thread."""
        self._loop = True
        while self._loop:
            if self.queue is not None:
                try:
                    obj, fname = self.queue.get(True, 1)
                except Queue.Empty:
                    print self.queue
                    continue

                obj.save(fname)
            else:
                time.sleep(1)

    def stop(self):
        """Stop writer."""
        self._loop = False
