"""Classes for handling segment gathering for Trollflow based Trollduction"""

import logging
import Queue
from threading import Thread
import time
import datetime as dt
import yaml
from collections import OrderedDict

from trollsift import Parser
from posttroll import message

SLOT_NOT_READY = 0
SLOT_READY = 1
SLOT_READY_BUT_WAIT_FOR_MORE = 2
SLOT_OBSOLETE_TIMEOUT = 3

DO_NOT_COPY_KEYS = ("uid", "uri", "channel_name", "segment")

class SegmentGathererContainer(object):

    """Container for SegmentGatherer instance"""

    logger = logging.getLogger("SegmentGathererContainer")

    def __init__(self, config):
        self.gatherer = None
        self._input_queue = None
        self.output_queue = Queue.Queue()
        self.thread = None

        # Create a SegmentGatherer instance
        self.gatherer = SegmentGatherer(config, self.input_queue,
                                        self.output_queue)

        # Start SegmentGatherer into a new daemonized thread.
        self.thread = Thread(target=self.gatherer.run)
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
        self.gatherer.input_queue = queue

    def __setstate__(self, state):
        self.__init__(**state)

    def stop(self):
        """Stop gatherer."""
        self.logger.debug("Stopping SegmentGatherer.")
        self.gatherer.stop()
        self.thread.join()
        self.logger.debug("SegmentGatherer stopped.")
        self.thread = None

class SegmentGatherer(Thread):

    """Class for gathering segments of one time slot together."""

    logger = logging.getLogger("SegmentGatherer")

    def __init__(self, config, input_queue, output_queue):
        Thread.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._loop = False
        self._parsers = []
        with open(config, 'r') as fid:
            self._config = yaml.load(fid)

        self._set_parsers()

        try:
            self._timeliness = \
                dt.timedelta(seconds=self._config["config"]["timeliness"])
        except KeyError:
            self._timeliness = dt.timedelta(seconds=1200)
        try:
            self._num_files_premature_publish = \
                self._config["config"]["num_files_premature_publish"]
        except KeyError:
            self._num_files_premature_publish = -1

        self.slots = OrderedDict()

        self.time_name = self._config["config"]["time_name"]

        self.logger = logging.getLogger("SegmentGatherer")

    def _clear_data(self, time_slot):
        """Clear data."""
        if time_slot in self.slots:
            del self.slots[time_slot]

    def _init_data(self, msg, mda):
        """Init wanted, all and critical files"""
        # Init metadata struct
        metadata = {}
        for key in msg.data:
            if key not in DO_NOT_COPY_KEYS:
                metadata[key] = msg.data[key]
        metadata['dataset'] = []

        # Use also metadata parsed from the filenames
        metadata.update(mda)

        time_slot = str(metadata[self.time_name])
        self.slots[time_slot] = {}
        self.slots[time_slot]['metadata'] = metadata.copy()

        # Critical files that are required, otherwise production will fail.
        # If there are no critical files, empty set([]) is used.
        #self.slots[time_slot]['critical_files'] = \
        self._compose_filenames(time_slot)

        self.slots[time_slot]['received_files'] = set([])
        self.slots[time_slot]['delayed_files'] = dict()
        self.slots[time_slot]['missing_files'] = set([])
        self.slots[time_slot]['timeout'] = None
        self.slots[time_slot]['files_till_premature_publish'] = \
            self._num_files_premature_publish

    def _set_parsers(self):
        """Set parsers"""
        files = self._config["files"]

        for fle in files:
            pattern = fle["pattern"]
            parser = Parser(pattern)
            self._parsers.append(parser)

    def _compose_filenames(self, time_slot):
        """Compose filename set()s"""

        # Get copy of metadata
        meta = self.slots[time_slot]['metadata'].copy()

        # Replace variable tags (such as processing time) with
        # wildcards, as these can't be forecasted.
        try:
            ignored_keys = self._config["config"]["variable_tags"].split(',')
            meta = _copy_without_ignore_items(meta, ignored_keys=ignored_keys)
        except KeyError:
            pass

        critical_files, wanted_files, all_files = [], [], []
        files = self._config["files"]

        for fle in files:
            pattern = fle["pattern"]
            parser = Parser(pattern)
            for seg in fle["segments"]:
                chans = seg.get('channel_name', [''])
                critical_segments = seg.get('critical_segments', [''])
                wanted_segments = seg.get('wanted_segments', [''])
                all_segments = seg.get('all_segments', [''])
                for chan in chans:
                    meta['channel_name'] = chan
                    for seg2 in critical_segments:
                        meta['segment'] = seg2
                        critical_files.append(parser.globify(meta))
                    for seg2 in wanted_segments:
                        meta['segment'] = seg2
                        wanted_files.append(parser.globify(meta))
                    for seg2 in all_segments:
                        meta['segment'] = seg2
                        all_files.append(parser.globify(meta))

        self.slots[time_slot]['critical_files'] = set(critical_files)
        self.slots[time_slot]['wanted_files'] = set(wanted_files)
        self.slots[time_slot]['all_files'] = set(all_files)

    def slot_ready(self, slot):
        """Determine if slot is ready to be published."""
        # If no files have been collected, return False
        if len(slot['received_files']) == 0:
            return SLOT_NOT_READY

        time_slot = str(slot['metadata'][self.time_name])

        wanted_and_critical_files = \
            slot['wanted_files'].union(slot['critical_files'])
        num_wanted_and_critical_files_received = \
            len(wanted_and_critical_files & slot['received_files'])

        # self.logger.debug("Got %d wanted or critical files in slot %s.",
        #                   num_wanted_and_critical_files_received,
        #                   time_slot)

        if num_wanted_and_critical_files_received \
                == slot['files_till_premature_publish']:
            slot['files_till_premature_publish'] = -1
            return SLOT_READY_BUT_WAIT_FOR_MORE

        # If all wanted files have been received, return True
        if wanted_and_critical_files.issubset(
                slot['received_files']):
            self.logger.info("All files received for slot %s.",
                             time_slot)
            return SLOT_READY

        if slot['critical_files'].issubset(slot['received_files']):
            # All critical files have been received
            if slot['timeout'] is None:
                # Set timeout
                slot['timeout'] = dt.datetime.utcnow() + self._timeliness
                self.logger.info("Setting timeout to %s for slot %s.",
                                 str(slot['timeout']),
                                 time_slot)
                return SLOT_NOT_READY
            elif slot['timeout'] < dt.datetime.utcnow():
                # Timeout reached, collection ready
                self.logger.info("Timeout occured, required files received "
                                 "for slot %s.", time_slot)
                return SLOT_READY
            else:
                pass
        else:
            if slot['timeout'] is None:
                slot['timeout'] = dt.datetime.utcnow() + self._timeliness
                self.logger.info("Setting timeout to %s for slot %s",
                                 str(slot['timeout']),
                                 time_slot)
                return SLOT_NOT_READY

            elif slot['timeout'] < dt.datetime.utcnow():
                # Timeout reached, collection is obsolete
                self.logger.warning("Timeout occured and required files "
                                    "were not present, data discarded for "
                                    "slot %s.",
                                    time_slot)
                return SLOT_OBSOLETE_TIMEOUT
            else:
                pass

        # Timeout not reached, wait for more files
        return SLOT_NOT_READY

    @property
    def loop(self):
        """Loop property"""
        return self._loop

    def run(self):
        """Run SegmentGatherer"""
        self._loop = True
        while self._loop:
            # Check if there are slots ready for publication
            slots = self.slots.copy()
            for slot in slots:
                slot = str(slot)
                status = self.slot_ready(slots[slot])
                if status == SLOT_READY:
                    # Collection ready, publish and remove
                    self._publish(slot)
                    self._clear_data(slot)
                if status == SLOT_READY_BUT_WAIT_FOR_MORE:
                    # Collection ready, publish and but wait for more
                    self._publish(slot, missing_files_check=False)
                elif status == SLOT_OBSOLETE_TIMEOUT:
                    # Collection unfinished and obslote, discard
                    self._clear_data(slot)
                else:
                    # Collection unfinished, wait for more data
                    pass

            # Check queue for new data
            msg = None
            if self.input_queue is not None:
                try:
                    msg = self.input_queue.get(True, 1)
                except KeyboardInterrupt:
                    self.stop()
                    continue
                except Queue.Empty:
                    continue
            else:
                time.sleep(1)
                continue

            if msg.type == "file":
                self.logger.info("New message received: %s", str(msg))
                self.process(msg)

    def stop(self):
        """Stop gatherer."""
        self.logger.info("Stopping gatherer.")
        self._loop = False

    def process(self, msg):
        """Process message"""

        mda = None
        for parser in self._parsers:
            try:
                mda = parser.parse(msg.data["uid"])
                break
            except ValueError:
                continue

        if mda is None:
            self.logger.debug("Unknown file, skipping.")
            return

        metadata = {}
        for key in msg.data:
            if key not in DO_NOT_COPY_KEYS:
                metadata[key] = msg.data[key]
        metadata.update(mda)

        time_slot = str(metadata[self.time_name])

        # Init metadata etc if this is the first file
        if time_slot not in self.slots:
            self._init_data(msg, mda)

        slot = self.slots[time_slot]

        # Replace variable tags (such as processing time) with
        # wildcards, as these can't be forecasted.
        try:
            variable_tags = self._config["config"]["variable_tags"].split(',')
            mda = _copy_without_ignore_items(mda, ignored_keys=variable_tags)
        except KeyError:
            pass

        mask = None
        for parser in self._parsers:
            try:
                mask = parser.globify(mda)
                break
            except ValueError:
                continue

        if mask is None or mask in slot['received_files']:
            return

        # Add uid and uri
        slot['metadata']['dataset'].append({'uri': msg.data['uri'],
                                            'uid': msg.data['uid']})

        # If critical files have been received but the slot is
        # not complete, add the file to list of delayed files
        if len(slot['critical_files']) > 0 and \
           slot['critical_files'].issubset(slot['received_files']):
            delay = dt.datetime.utcnow() - (slot['timeout'] - self._timeliness)
            slot['delayed_files'][msg.data['uid']] = delay.total_seconds()

        # Add to received files
        slot['received_files'].add(mask)

    def _publish(self, time_slot, missing_files_check=True):
        """Publish file dataset and reinitialize gatherer."""

        data = self.slots[time_slot]

        # Diagnostic logging about delayed ...
        delayed_files = data['delayed_files']
        if len(delayed_files) > 0:
            file_str = ''
            for key in delayed_files:
                file_str += "%s %f seconds, " % (key, delayed_files[key])
            self.logger.warning("Files received late: %s", file_str.strip(', '))

        if missing_files_check:
            # and missing files
            missing_files = data['all_files'].difference(data['received_files'])
            if len(missing_files) > 0:
                self.logger.warning("Missing files: %s",
                                    ', '.join(missing_files))

        # Although we're not publishing a message, generate one anyway
        # for compatibility
        msg = message.Message("/placeholder", "dataset", data['metadata'])
        self.logger.info("Forwarding: %s", str(msg))
        self.output_queue.put(msg)


def _copy_without_ignore_items(the_dict, ignored_keys=['ignore']):
    """
    get a copy of *the_dict* without entries having substring
    'ignore' in key
    """
    new_dict = {}
    for (key, val) in list(the_dict.items()):
        if key not in ignored_keys:
            new_dict[key] = val
    return new_dict
