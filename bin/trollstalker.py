#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014, 2015

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

"""./trollstalker.py -c /path/to/trollstalker_config.ini -C noaa_hrpt
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
import os.path

LOGGER = logging.getLogger(__name__)


class EventHandler(ProcessEvent):

    """
    Event handler class for inotify.
     *topic* - topic of the published messages
     *posttroll_port* - port number to publish the messages on
     *filepattern* - filepattern for finding information from the filename
    """

    def __init__(self, topic, instrument, posttroll_port=0, filepattern=None,
                 aliases=None, tbus_orbit=False):
        super(EventHandler, self).__init__()

        self._pub = NoisyPublisher("trollstalker", posttroll_port, topic)
        self.pub = self._pub.start()
        self.topic = topic
        self.info = {}
        if filepattern is None:
            filepattern = '{filename}'
        self.file_parser = Parser(filepattern)
        self.instrument = instrument
        self.aliases = aliases
        self.tbus_orbit = tbus_orbit

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
        LOGGER.debug("trigger: IN_CLOSE_WRITE")
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
        LOGGER.debug("trigger: IN_MODIFY")
        self.process(event)

    def process(self, event):
        '''Process the event'''
        # New file created and closed
        if not event.dir:
            LOGGER.debug("processing %s", event.pathname)
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
        return Message(self.topic, 'file', self.info)

    def parse_file_info(self, event):
        '''Parse satellite and orbit information from the filename.
        Message is sent, if a matching filepattern is found.
        '''
        try:
            LOGGER.debug("filter: %s\t event: %s",
                         self.file_parser.fmt, event.pathname)
            self.info = self.file_parser.parse(
                os.path.basename(event.pathname))
            LOGGER.debug("Extracted: %s", str(self.info))
        except ValueError:
            # Filename didn't match pattern, so empty the info dict
            LOGGER.info("Couldn't extract any usefull information")
            self.info = {}
        else:
            self.info['uri'] = event.pathname
            self.info['uid'] = os.path.basename(event.pathname)
            self.info['sensor'] = self.instrument.split(',')
            LOGGER.debug("self.info['sensor']: " + str(self.info['sensor']))

            if self.tbus_orbit and "orbit_number" in self.info:
                LOGGER.info("Changing orbit number by -1!")
                self.info["orbit_number"] -= 1

            # replace values with corresponding aliases, if any are given
            if self.aliases:
                for key in self.info:
                    if key in self.aliases:
                        self.info[key] = self.aliases[key][str(self.info[key])]


class NewThreadedNotifier(ThreadedNotifier):

    '''Threaded notifier class
    '''

    def stop(self, *args, **kwargs):
        self._default_proc_fun.stop()
        ThreadedNotifier.stop(self, *args, **kwargs)


def create_notifier(topic, instrument, posttroll_port, filepattern,
                    event_names, monitored_dirs, aliases=None,
                    tbus_orbit=False):
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

    event_handler = EventHandler(topic, instrument,
                                 posttroll_port=posttroll_port,
                                 filepattern=filepattern,
                                 aliases=aliases,
                                 tbus_orbit=tbus_orbit)
    notifier = NewThreadedNotifier(manager, event_handler)

    # Add directories and event masks to watch manager
    for monitored_dir in monitored_dirs:
        manager.add_watch(monitored_dir, event_mask, rec=True)

    return notifier


def parse_aliases(config):
    '''Parse aliases from the config.

    Aliases are given in the config as:

    {'alias_<name>': 'value:alias'}, or
    {'alias_<name>': 'value1:alias1|value2:alias2'},

    where <name> is the name of the key which value will be
    replaced. The later form is there to support several possible
    substitutions (eg. '2' -> '9' and '3' -> '10' in the case of MSG).

    '''
    aliases = {}

    for key in config:
        if 'alias' in key:
            alias = config[key]
            new_key = key.replace('alias_', '')
            if '|' in alias or ':' in alias:
                parts = alias.split('|')
                aliases2 = {}
                for part in parts:
                    key2, val2 = part.split(':')
                    aliases2[key2] = val2
                alias = aliases2
            aliases[new_key] = alias
    return aliases


def main():
    '''Main(). Commandline parsing and stalker startup.'''

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--monitored_dirs", dest="monitored_dirs",
                        nargs='+',
                        type=str,
                        default=[],
                        help="Names of the monitored directories "
                        "separated by space")
    parser.add_argument("-p", "--posttroll_port", dest="posttroll_port",
                        default=0, type=int,
                        help="Local port where messages are published")
    parser.add_argument("-t", "--topic", dest="topic",
                        type=str,
                        default=None,
                        help="Topic of the sent messages")
    parser.add_argument("-c", "--configuration_file",
                        type=str,
                        help="Name of the config.ini configuration file")
    parser.add_argument("-C", "--config_item",
                        type=str,
                        help="Name of the configuration item to use")
    parser.add_argument("-e", "--event_names",
                        type=str, default=None,
                        help="Name of the pyinotify events to monitor")
    parser.add_argument("-f", "--filepattern",
                        type=str,
                        help="Filepattern used to parse "
                        "satellite/orbit/date/etc information")
    parser.add_argument("-i", "--instrument",
                        type=str, default=None,
                        help="Instrument name in the satellite")

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

    posttroll_port = args.posttroll_port
    topic = args.topic
    event_names = args.event_names
    instrument = args.instrument

    filepattern = args.filepattern
    if args.filepattern == '':
        filepattern = None

    if args.configuration_file is not None:
        config_fname = args.configuration_file

        if "template" in config_fname:
            print "Template file given as trollstalker logging config," \
                " aborting!"
            sys.exit()

        config = ConfigParser()
        config.read(config_fname)
        config = dict(config.items(args.config_item))
        config['name'] = args.configuration_file

        topic = topic or config['topic']
        monitored_dirs = monitored_dirs or config['directory']
        filepattern = filepattern or config['filepattern']
        try:
            posttroll_port = posttroll_port or int(config['posttroll_port'])
        except (KeyError, ValueError):
            if posttroll_port is None:
                posttroll_port = 0
        try:
            filepattern = filepattern or config['filepattern']
        except KeyError:
            pass
        try:
            event_names = event_names or config['event_names']
        except KeyError:
            pass
        try:
            instrument = instrument or config['instruments']
        except KeyError:
            pass
        aliases = parse_aliases(config)
        tbus_orbit = bool(config.get("tbus_orbit", False))
        try:
            log_config = config["stalker_log_config"]
        except KeyError:
            try:
                loglevel = getattr(logging, config["loglevel"])
                if loglevel == "":
                    raise AttributeError
            except AttributeError:
                loglevel = logging.DEBUG
            LOGGER.setLevel(loglevel)

            strhndl = logging.StreamHandler()
            strhndl.setLevel(loglevel)
            log_format = "[%(asctime)s %(levelname)-8s %(name)s] %(message)s"
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
    notifier = create_notifier(topic, instrument, posttroll_port, filepattern,
                               event_names, monitored_dirs, aliases=aliases,
                               tbus_orbit=tbus_orbit)
    notifier.start()

    try:
        while True:
            time.sleep(6000000)
    except KeyboardInterrupt:
        LOGGER.info("Interupting TrollStalker")
    finally:
        notifier.stop()

if __name__ == "__main__":
    LOGGER = logging.getLogger("trollstalker")
    main()
