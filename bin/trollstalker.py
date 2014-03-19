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

"""./trollstalker.py -d /tmp/data/new/ -p 9000 -m EPI -t 'HRIT lvl1.5'
"""

import argparse
import logging, logging.handlers
from pyinotify import WatchManager, ThreadedNotifier, \
    ProcessEvent, IN_CLOSE_WRITE, IN_CLOSE_NOWRITE
import fnmatch
import sys
import time

from posttroll.publisher import NoisyPublisher
from posttroll.message import Message
from trollduction import xml_read

class EventHandler(ProcessEvent):
    """
    Event handler class for inotify.
    """
    def __init__(self, file_tags, publish_port=0, filepattern_fname=None):
        super(EventHandler, self).__init__()
        
        self.logger = logging.getLogger(__name__)
        self._pub = NoisyPublisher("trollstalker", publish_port, file_tags)
        self.file_tags = file_tags
        self.pub = self._pub.start()
        self.subject = ''
        self.info = {}
        self.msg_type = ''
        self.filepattern_fname = filepattern_fname


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
    

    def process_IN_CLOSE(self, event):
        """When a file is closed, publish a message.
        """
        self.logger.debug("new file created and closed %s" %event.pathname)
        # New file created and closed
        if not event.dir:
            # parse information and create self.info dict{}
            self.parse_file_info(event)
            if self.msg_type != '':
                message = self.create_message()            
                print "Publishing message %s" % str(message)
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
        #xml_dict = xml_read.parse_xml(xml_read.get_root('/tmp/foo.xml'))

        # Search for a matching file pattern
        for pattern in xml_dict['pattern']:
            if pattern['msg_type'] not in self.file_tags:
                continue
            if fnmatch.fnmatch(event.name, pattern['file_pattern']):
                self.msg_type = pattern['msg_type']
                self.subject = "/" + self.msg_type + "/NewFileArrived/"
                # Parse info{} dict
                #self.info = {}
                self.info['uri'] = event.pathname
                parts = event.name.split(pattern['split_char'])
                
                info = pattern['info']
                for key in info.keys():
                    if isinstance(info[key], dict):
                        part = parts[int(info[key]['part'])]
                        if info[key].has_key('strip_char'):
                            part = part.strip(info[key]['strip_char'])
                        if info[key].has_key('chars'):
                            part = eval('part['+info[key]['chars']+']')
                        if info[key].has_key('text_pattern'):
                            if info[key]['text_pattern'] in part:
                                part = 1
                            else:
                                part = 0
                        if info[key].has_key('add_int'):
                            part = str(int(part)+int(info[key]['add_int']))
                        self.info[key] = part
                    else:
                        self.info[key] = pattern['info'][key]
                return

        # No match, so the self.info{} will be empty

    
def main():
    '''Main(). Commandline parsing and stalker startup.
    '''

    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser() 
    
    parser.add_argument("-d", "--monitored_dirs", dest="monitored_dirs",
                        nargs='+',
                        type=str,
                        default='.',
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
                        dest="configuration_file",
                        default="", type=str, 
                        help="Name of the xml configuration file")

    parser.add_argument("-f", "--filepattern_file",
                        dest="filepattern_file",
                        default="", type=str, 
                        help="Name of the xml configuration file")

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit()
    else:
        args = parser.parse_args()

    # Parse commandline arguments.  If configuration file is given, it
    # overrides everything else.
    try:
        config_fname = args.configuration_file
        config = xml_read.parse_xml(xml_read.get_root(config_fname))
        file_tags = config['file_tag']
        monitored_dirs = config['directory']
        try:
            publish_port = int(config['publish_port'])
        except KeyError:
            publish_port = 0
        try:
            filepattern_fname = config['filepattern_file']
        except KeyError:
            filepattern_fname = None
    except AttributeError:
        # Check other commandline arguments
        monitored_dirs = args.monitored_dirs
        publish_port = args.publish_port
        file_tags = args.file_tags
        if args.filepattern_file == '':
            filepattern_fname = None
        else:
            filepattern_fname = args.filepattern_file


    #Event handler observes the operations in defined folder   
    manager = WatchManager()
    events = [IN_CLOSE_WRITE, IN_CLOSE_NOWRITE] # monitored events
    
    event_handler = EventHandler(file_tags,
                                 publish_port=publish_port,
                                 filepattern_fname=filepattern_fname)
    notifier = ThreadedNotifier(manager, event_handler)

    # Add directories and event masks to watch manager
    for monitored_dir in monitored_dirs:
        for event in events:
            manager.add_watch(monitored_dir, event, rec = True)
    
    # Start watching for new files
    notifier.start()

    try:
        while True:
            time.sleep(6000000)
    except KeyboardInterrupt:
        print "Interupting TrollStalker"
    finally:
        event_handler.stop()
        notifier.stop()

if __name__ == "__main__":
    main()
