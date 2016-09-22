
import Queue
from threading import Thread
import logging
import time

class DataWriterContainer(object):

    '''Container for DataWriter instance
    '''

    logger = logging.getLogger("DataWriterContainer")

    def __init__(self, topic=None, port=0, nameservers=[],
                 save_settings=None):
        self.topic = topic
        self._input_queue = None
        self.output_queue = Queue.Queue()
        self.thread = None

        # Create a Writer instance
        self.writer = DataWriter(queue=self.input_queue,
                                 save_settings=save_settings)
        # Start Writer instance into a new daemonized thread.
        self.thread = Thread(target=self.writer.run)
        self.thread.setDaemon(True)
        self.thread.start()

    @property
    def input_queue(self):
        """Property writer"""
        return self._input_queue

    @input_queue.setter
    def input_queue(self, queue):
        """Set writer queue"""
        self._input_queue = queue
        self.writer.queue = queue

    def __setstate__(self, state):
        self.__init__(**state)

    def restart(self):
        '''Restart writer after configuration update.
        '''
        if self.writer is not None:
            if self.writer.loop:
                self.stop()
        self.__init__()

    def stop(self):
        '''Stop writer.'''
        self.logger.debug("Stopping writer.")
        self.writer.stop()
        self.thread.join()
        self.logger.debug("Writer stopped.")
        self.thread = None

class DataWriter(Thread):
    """Writes data to disk.
    """

    logger = logging.getLogger("DataWriter")

    def __init__(self, queue=None, save_settings=None):
        Thread.__init__(self)
        self.queue = queue
        self._loop = False
        self._save_settings = save_settings

    def run(self):
        """Run the thread."""
        self._loop = True
        # Parse settings for saving
        compression = self._save_settings.get('compression', 6)
        tags = self._save_settings.get('tags', None)
        fformat = self._save_settings.get('fformat', None)
        gdal_options = self._save_settings.get('gdal_options', None)
        blocksize = self._save_settings.get('blocksize', None)

        while self._loop:
            if self.queue is not None:
                try:
                    obj, fname = self.queue.get(True, 1)
                except Queue.Empty:
                    continue
                self.logger.info("Saving %s", fname)
                obj.save(fname, compression=compression, tags=tags,
                         fformat=fformat, gdal_options=gdal_options,
                         blocksize=blocksize)
                self.logger.info("Saved %s", fname)
            else:
                time.sleep(1)

    def stop(self):
        """Stop writer."""
        self._loop = False

    @property
    def loop(self):
        """Property loop"""
        return self._loop
