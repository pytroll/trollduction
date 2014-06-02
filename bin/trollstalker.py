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
import fnmatch
import time
import subprocess
from threading import Thread
import Queue
import os

try:
    from posttroll.publisher import NoisyPublisher
    from posttroll.message import Message
    from trollduction import xml_read
    USE_MESSAGING = True
except ImportError:
    USE_MESSAGING = False

import logging
from ConfigParser import ConfigParser

LOGGER = logging.getLogger("trollstalker")


class EventHandler(ProcessEvent):
    """
    Event handler class for inotify.
    *file_tags* - tags for published messages
    *publish_port* - port number to publish the messages on
    *filepattern_fname* - file containing the information how to parse messages
    *command* - system command or script to run for each matching file
    *pattern* - file pattern to which files are compared. If a match,
                run the associated command
    """
    def __init__(self, file_tags, publish_port=0, filepattern_fname=None,
                 command=None, pattern=None):
        super(EventHandler, self).__init__()

        self.file_tags = file_tags
        if USE_MESSAGING:
            self._pub = NoisyPublisher("trollstalker", publish_port, file_tags)
            self.pub = self._pub.start()
            self.subject = ''
            self.info = {}
            self.msg_type = ''
            self.filepattern_fname = filepattern_fname
        self.command = command
        if self.command is not None:
            self.file_queue = Queue.Queue()
            self.command_thread = Thread(target=self.run_command)
            self.command_thread.setDaemon(True)
            self.command_thread.start()
        self.pattern = pattern

    def stop(self):
        '''Stop publisher, close the file queue and join the command thread.
        '''
        self.file_queue.put(None)
        if USE_MESSAGING:
            self._pub.stop()
        if self.command is not None:
            self.file_queue.join()
            self.command_thread.join()

    def __clean__(self):
        '''Clean instance attributes.
        '''
        self.subject = ''
        self.info = {}
        self.msg_type = ''


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

        if not event.dir:
            if USE_MESSAGING:
                # parse information and create self.info dict{}
                self.parse_file_info(event)
                if self.msg_type != '':
                    message = self.create_message()
                    LOGGER.debug("Publishing message %s", str(message))
                    self.pub.send(str(message))
                self.__clean__()
            if self.command:
                # Add file path to queue
                self.file_queue.put(event.pathname)


    def run_command(self):
        '''Run external command'''

        while True:
            try:
                filename = self.file_queue.get(timeout=1)
            except Queue.Empty:
                continue

            if filename is None:
                self.file_queue.task_done()
                break

            if self.pattern is not None:
                if not fnmatch.fnmatch(os.path.basename(filename),
                                       self.pattern):
                    self.file_queue.task_done()
                    continue
            proc = subprocess.Popen([self.command, filename],
                                    shell=False,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            (stdout, stderr) = proc.communicate()
            proc.wait()

            if proc.returncode > 0:
                LOGGER.critical('Command returned failure')
                LOGGER.critical(stderr)
            else:
                LOGGER.info('Command succeeded')
                LOGGER.info(stdout)
            self.file_queue.task_done()


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
        #xml_dict = xml_read.parse_xml(xml_read.get_root('/tmp/foo.xml'))

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
                    event_names, monitored_dirs, command, pattern):
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

    event_handler = EventHandler(file_tags,
                                 publish_port=publish_port,
                                 filepattern_fname=filepattern_fname,
                                 command=command, pattern=pattern)
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

    parser.add_argument("-t", "--file-tags", dest="file_tags",
                        type=str,
                        nargs='+',
                        default=[],
                        help="Identifier for monitored files")

    parser.add_argument("-c", "--configuration_file",
                        type=str,
                        help="Name of the configuration file")

    parser.add_argument("-C", "--config_item",
                        type=str,
                        help="Name of the configuration item to use")

    parser.add_argument("-f", "--filepattern_file",
                        type=str,
                        help="Name of the xml filepattern file")

    parser.add_argument("-e", "--event_names",
                        type=str, default=None,
                        help="Name of the pyinotify events to monitor")

    parser.add_argument("-D", "--debug", default=False,
                        dest="debug", action='store_true',
                        help="Enable debug messages")

    parser.add_argument("-r", "--run_command", default=None,
                        type=str,
                        help="Name of the command that is run.")

    parser.add_argument("-l", "--log_config", default=None,
                        type=str,
                        help="Name of the file for log config")

    parser.add_argument("-P", "--file_pattern", default=None,
                        type=str,
                        help="Filename pattern for matching event-triggering"+\
                            " files")

    # Parse commandline arguments.  If command line args are given, they
    # override the configuration file.

    args = parser.parse_args()

    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = None #logging.INFO

    # Check first commandline arguments
    monitored_dirs = args.monitored_dirs
    if monitored_dirs == '':
        monitored_dirs = None

    publish_port = args.publish_port or None

    file_tags = args.file_tags

    filepattern_fname = args.filepattern_file
    if args.filepattern_file == '':
        filepattern_fname = None

    event_names = args.event_names

    pattern = args.file_pattern

    log_config = args.log_config

    command = args.run_command

    if args.configuration_file is not None:
        config_fname = args.configuration_file
        config = ConfigParser()
        config.read(config_fname)
        config = dict(config.items(args.config_item))
        config['name'] = args.configuration_file

        file_tags = file_tags or config['file_tag']
        monitored_dirs = monitored_dirs or config['directory']
        try:
            publish_port = publish_port or int(config['publish_port'])
        except (KeyError, ValueError):
            if publish_port is None:
                publish_port = 0
        try:
            filepattern_fname = filepattern_fname or config['filepattern_file']
        except KeyError:
            pass
        try:
            event_names = event_names or config['event_names']
        except KeyError:
            pass
        try:
            loglevel = loglevel or getattr(logging, config['loglevel'])
        except KeyError:
            pass
        try:
            command = command or config['command']
        except KeyError:
            pass
        try:
            pattern = pattern or config['pattern']
        except KeyError:
            pass
        try:
            log_config = log_config or config["log_config"]
        except KeyError:
            logging.basicConfig()
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
    notifier = create_notifier(file_tags, publish_port,
                               filepattern_fname, event_names,
                               monitored_dirs, command, pattern)
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
