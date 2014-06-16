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

"""./trollstalker.py -d /tmp/data/new/ -p 9000 -m EPI -t HRPT_l1b  or
   ./trollstalker.py -c /path/to/trollstalker_config.xml
"""

import argparse
from pyinotify import WatchManager, ThreadedNotifier, \
    ProcessEvent, IN_CLOSE_WRITE, IN_MOVED_TO
import fnmatch
import time

from posttroll.publisher import NoisyPublisher
from posttroll.message import Message
from trollduction import xml_read
import logging

LOGGER = logging.getLogger("trollstalker")

class EventHandler(ProcessEvent):
    """
    Event handler class for inotify.
    """
    def __init__(self, file_tags, publish_port=0, filepattern_fname=None,
                 debug=False):
        super(EventHandler, self).__init__()

        self._pub = NoisyPublisher("trollstalker", publish_port, file_tags)
        self.file_tags = file_tags
        self.pub = self._pub.start()
        self.subject = ''
        self.info = {}
        self.msg_type = ''
        self.filepattern_fname = filepattern_fname
        self.debug = debug

    def stop(self):
        '''Stop publisher.
        '''
        self._pub.stop()


    def __clean__(self):
        '''Clean instance attributes.
        '''
        self.subject = ''
        self.info = {}
        self.msg_type = ''


    def process_IN_CLOSE_WRITE(self, event):
        """When a file is closed, publish a message.
        """
        LOGGER.debug("trigger: IN_MOVED_TO")
        self.process(event)


    def process_IN_MOVED_TO(self, event):
        """When a file is closed, publish a message.
        """
        LOGGER.debug("trigger: IN_MOVED_TO")
        self.process(event)


    def process(self, event):
        '''Process new file'''
        # New file created and closed
        if not event.dir:
            # parse information and create self.info dict{}
            self.parse_file_info(event)
            if self.msg_type != '':
                message = self.create_message()
                LOGGER.debug("Publishing message %s", str(message))
                self.pub.send(str(message))
            self.__clean__()


    def create_message(self):
        """Create broadcasted message
        """
        return Message(self.subject, str(self.msg_type), self.info)


    def parse_file_info(self, event):
        '''Parse satellite and orbit information from the filename.
        Message is sent, if a matching filepattern is found.
        '''
        # Read configuration file
        xml_dict = xml_read.get_filepattern_config(fname=self.filepattern_fname)
        # xml_dict = xml_read.parse_xml(xml_read.get_root('/tmp/foo.xml'))

        # Search for a matching file pattern
        for pattern in xml_dict['pattern']:
            if pattern['msg_type'] not in self.file_tags:
                continue
            if fnmatch.fnmatch(event.name, pattern['file_pattern']):
                self.msg_type = pattern['msg_type']
                self.subject = "/" + self.msg_type + "/NewFileArrived/"
                self.info['uri'] = event.pathname
                parts = event.name.split(pattern['split_char'])

                info = pattern['info']
                for key in info.keys():
                    if isinstance(info[key], dict):
                        part = parts[int(info[key]['part'])]
                        if 'strip_char' in info[key]:
                            part = part.strip(info[key]['strip_char'])
                        if 'chars' in info[key]:
                            part = eval('part['+info[key]['chars']+']')
                        if 'text_pattern' in info[key]:
                            if info[key]['text_pattern'] in part:
                                part = 1
                            else:
                                part = 0
                        if 'add_int' in info[key]:
                            part = str(int(part)+int(info[key]['add_int']))
                        self.info[key] = part
                    else:
                        self.info[key] = pattern['info'][key]
                return

        # No match, so the self.info{} will be empty

class NewThreadedNotifier(ThreadedNotifier):
    '''Threaded notifier class
    '''
    def stop(self, *args, **kwargs):
        self._default_proc_fun.stop()
        ThreadedNotifier.stop(self, *args, **kwargs)

def create_notifier(file_tags, publish_port, filepattern_fname, 
                    *monitored_dirs):
    '''Create new notifier'''
    # Event handler observes the operations in defined folder
    manager = WatchManager()
    events = IN_CLOSE_WRITE | IN_MOVED_TO # monitored event(s)

    event_handler = EventHandler(file_tags,
                                 publish_port=publish_port,
                                 filepattern_fname=filepattern_fname)
    notifier = NewThreadedNotifier(manager, event_handler)

    # Add directories and event masks to watch manager
    for monitored_dir in monitored_dirs:
        manager.add_watch(monitored_dir, events, rec=True)

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

    parser.add_argument("-t", "--file-tags", dest="file_tags",
                        type=str,
                        nargs='+',
                        default=[],
                        help="Identifier for monitored files")

    parser.add_argument("-c", "--configuration_file",
                        type=str,
                        help="Name of the xml configuration file")

    parser.add_argument("-f", "--filepattern_file",
                        type=str,
                        help="Name of the xml filepattern file")
    parser.add_argument("-D", "--debug", default=False,
                        dest="debug", action='store_true',
                        help="Enable debug messages")

    args = parser.parse_args()

    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO


    # LOGGER = logging.getLogger("")
    LOGGER.setLevel(loglevel)

    strhndl = logging.StreamHandler()
    strhndl.setLevel(loglevel)
    log_format = "[%(asctime)s %(levelname)-8s] %(name)s: %(message)s"
    formatter = logging.Formatter(log_format)

    strhndl.setFormatter(formatter)
    LOGGER.addHandler(strhndl)

    # LOGGER = logging.getLogger("trollstalker")
    LOGGER.setLevel(loglevel)
    LOGGER.debug("started logger")

    # Parse commandline arguments.  If command line args are given, it
    # overrides the configuration file.

    # Check first commandline arguments
    monitored_dirs = args.monitored_dirs
    if monitored_dirs == '':
        monitored_dirs = None

    publish_port = args.publish_port

    file_tags = args.file_tags

    filepattern_fname = args.filepattern_file
    if args.filepattern_file == '':
        filepattern_fname = None

    if args.configuration_file is not None:
        config_fname = args.configuration_file
        config = xml_read.parse_xml(xml_read.get_root(config_fname))
        file_tags = file_tags or config['file_tag']
        monitored_dirs = monitored_dirs or config['directory']
        try:
            publish_port = publish_port or int(config['publish_port'])
        except KeyError:
            if publish_port is None:
                publish_port = 0
        try:
            filepattern_fname = filepattern_fname or config['filepattern_file']
        except KeyError:
            pass

    # Start watching for new files
    notifier = create_notifier(file_tags, publish_port,
                               filepattern_fname, *monitored_dirs)
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
