#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014

# Author(s):

#   Joonas Karjalainen <joonas.karjalainen@fmi.fi>
#   Panu Lahtinen <panu.lahtinen@fmi.fi>
#   Martin Raspaud <martin.raspaud@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""./trollstalker.py -c ../examples/trollstalker_config.cfg -C msg_hrit
"""

import argparse
from pyinotify import WatchManager, ThreadedNotifier, ProcessEvent
import pyinotify
import sys
import time
from posttroll.publisher import NoisyPublisher
from posttroll.message import Message
from trollsift import Parser
from ConfigParser import ConfigParser
import logging
import logging.config

LOGGER = logging.getLogger("trollstalker")

class EventHandler(ProcessEvent):
    """
    Event handler class for inotify.
     *subject* - subject line of the published messages
     *publish_port* - port number to publish the messages on
     *filepattern* - filepattern for finding information from the filename
    """
    def __init__(self, subject, publish_port=0, filepattern=None):
        super(EventHandler, self).__init__()
        
        self._pub = NoisyPublisher("trollstalker", publish_port, subject)
        self.pub = self._pub.start()
        self.subject = subject
        self.info = {}
        if filepattern is None:
            filepattern = '{filename}'
        self.file_parser = Parser(filepattern)

    def stop(self):
        '''Stop publisher.
        '''
        self._pub.stop()

    def __clean__(self):
        '''Clean instance attributes.
        '''
        self.info = {}

    def process_IN_CLOSE_WRITE(self, event):
        """When a file is closed, process the associated event.
        """
        LOGGER.debug("trigger: IN_MOVED_TO")
        self.process(event)

    def process_IN_CLOSE_NOWRITE(self, event):
        """When a nonwritable file is closed, process the associated event.
        """
        LOGGER.debug("trigger: IN_CREATE")
        self.process(event)

    def process_IN_MOVED_TO(self, event):
        """When a file is closed, process the associated event.
        """
        LOGGER.debug("trigger: IN_MOVED_TO")
        self.process(event)

    def process_IN_CREATE(self, event):
        """When a file is created, process the associated event.
        """
        LOGGER.debug("trigger: IN_CREATE")
        self.process(event)

    def process_IN_CLOSE_MODIFY(self, event):
        """When a file is modified and closed, process the associated event.
        """
        LOGGER.debug("trigger: IN_CREATE")
        self.process(event)

    def process(self, event):
        '''Process the event'''
        # New file created and closed
        if not event.dir:
            # parse information and create self.info dict{}
            self.parse_file_info(event)
            if len(self.info) > 0:
                message = self.create_message()
                LOGGER.info("Publishing message %s" % str(message))
                self.pub.send(str(message))
            self.__clean__()


    def create_message(self):
        """Create broadcasted message
        """
        return Message(self.subject, 'file', self.info)


    def parse_file_info(self, event):
        '''Parse satellite and orbit information from the filename.
        Message is sent, if a matching filepattern is found.
        '''
        try:
            self.info = self.file_parser.parse(event.pathname)
        except ValueError:
            # Filename didn't match pattern, so empty the info dict
            self.info = {}

class NewThreadedNotifier(ThreadedNotifier):
    '''Threaded notifier class
    '''
    def stop(self, *args, **kwargs):
        self._default_proc_fun.stop()
        ThreadedNotifier.stop(self, *args, **kwargs)


def create_notifier(subject, publish_port, filepattern,
                    event_names, monitored_dirs):
    '''Create new notifier'''

    # Event handler observes the operations in defined folder
    manager = WatchManager()

    # Collect mask for events that are monitored
    if type(event_names) is not list:
        event_names = event_names.split(',')
    event_mask = 0
    for event in event_names:
        try:
            event_mask |= getattr(pyinotify, event)
        except AttributeError:
            LOGGER.warning('Event ' + event + ' not found in pyinotify')

    event_handler = EventHandler(subject,
                                 publish_port=publish_port,
                                 filepattern=filepattern)
    notifier = NewThreadedNotifier(manager, event_handler)

    # Add directories and event masks to watch manager
    for monitored_dir in monitored_dirs:
        manager.add_watch(monitored_dir, event_mask, rec=True)

    return notifier


def main():
    '''Main(). Commandline parsing and stalker startup.'''

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--monitored_dirs", dest="monitored_dirs",
                        nargs='+',
                        type=str,
                        default=[],
                        help="Names of the monitored directories "\
                            "separated by space")
    parser.add_argument("-p", "--publish_port", dest="publish_port",
                      default=0, type=int,
                      help="Local port where messages are published")
    parser.add_argument("-s", "--subject", dest="subject",
                        type=str,
                        default=None,
                        help="Subject of the sent message")
    parser.add_argument("-c", "--configuration_file",
                        type=str,
                        help="Name of the xml configuration file")
    parser.add_argument("-C", "--config_item",
                        type=str,
                        help="Name of the configuration item to use")
    parser.add_argument("-e", "--event_names",
                        type=str, default=None,
                        help="Name of the pyinotify events to monitor")
    parser.add_argument("-f", "--filepattern",
                        type=str,
                        help="Filepattern used to parse " \
                            "satellite/orbit/date/etc information")

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit()
    else:
        args = parser.parse_args()

    # Parse commandline arguments.  If args are given, they override
    # the configuration file.

    # Check first commandline arguments
    monitored_dirs = args.monitored_dirs
    if monitored_dirs == '':
        monitored_dirs = None

    publish_port = args.publish_port
    subject = args.subject
    event_names = args.event_names

    filepattern = args.filepattern
    if args.filepattern == '':
        filepattern = None

    if args.configuration_file is not None:
        config_fname = args.configuration_file

        config = ConfigParser()
        config.read(config_fname)
        config = dict(config.items(args.config_item))
        config['name'] = args.configuration_file

        subject = subject or config['subject']
        monitored_dirs = monitored_dirs or config['directory']
        filepattern = filepattern or config['filepattern']
        try:
            publish_port = publish_port or int(config['publish_port'])
        except (KeyError, ValueError):
            if publish_port is None:
                publish_port = 0
        try:
            filepattern = filepattern or config['filepattern']
        except KeyError:
            pass
        try:
            event_names = event_names or config['event_names']
        except KeyError:
            pass
        try:
            log_config = config["log_config"]
        except KeyError:
            logging.basicConfig()
            try:
                loglevel = getattr(logging, config["loglevel"])
            except AttributeError:
                loglevel = logging.DEBUG
            LOGGER.setLevel(loglevel)

            strhndl = logging.StreamHandler()
            strhndl.setLevel(loglevel)
            log_format = "[%(asctime)s %(levelname)-8s] %(name)s: %(message)s"
            formatter = logging.Formatter(log_format)

            strhndl.setFormatter(formatter)
            LOGGER.addHandler(strhndl)
        else:
            logging.config.fileConfig(log_config)

    event_names = event_names or 'IN_CLOSE_WRITE,IN_MOVED_TO'

    LOGGER.debug("Logger started")

    if type(monitored_dirs) is not list:
        monitored_dirs = [monitored_dirs]

    # Start watching for new files
    notifier = create_notifier(subject, publish_port, filepattern, event_names,
                               monitored_dirs)
    notifier.start()

    try:
        while True:
            time.sleep(6000000)
    except KeyboardInterrupt:
        LOGGER.info("Interupting TrollStalker")
    finally:
        notifier.stop()

if __name__ == "__main__":
    main()
