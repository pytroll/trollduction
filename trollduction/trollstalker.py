#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013

# Author(s):

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

import argparse
import logging, logging.handlers
from pyinotify import WatchManager, Notifier, ProcessEvent
import pyinotify
import fnmatch
import sys
import os

from posttroll.publisher import Publisher, get_own_ip
from posttroll.message import Message


class EventHandler(ProcessEvent):
    """
    Event handler class for inotify.
    """
    def __init__(self, filetypes, publish_port = 9000):
        super(EventHandler, self).__init__()
        
        self.logger = logging.getLogger(__name__)
        pub_address = "tcp://" + str(get_own_ip()) + ":" + str(publish_port)
        self.pub = Publisher(pub_address)
        self.filetypes = filetypes
        self.filename = ''
        self.info = {}
        self.filetype = ''
        self.subject = '/NewFileArrived'
        
    def __clean__(self):
        self.filename = ''
        self.filetype = ''
        self.info = ''
        self.filepath = ''
        self.fullname = ''
        self.satellite = ''
        self.satnumber = ''
        self.year = ''
        self.month = ''
        self.day = ''
        self.hour = ''
        self.minute = ''
        self.instrument = ''
        self.orbit = ''
    
    """
    def is_config_changed(self):
        if os.stat(self.config_file).st_mtime > self.config_mtime:
            return True
    
    def update_config_mtime(self):
        self.config_mtime = os.stat(self.config_file).st_mtime
    
    """
        
    def process_IN_CREATE(self, event):
        """
        When new file is created, publish message
        """
        self.logger.debug("new file created %s" %event.pathname)
        #print event.__dict__
        # New file created
        if not event.dir:
            """            
            if self.is_config_changed():
                self.update_config_mtime()
                self.parse_config()
            """
            self.parse_file_info(event)
            self.info = {"uri": self.fullname,
                         "satellite": self.satellite,
                         "satnumber": self.satnumber,
                         "instrument": self.instrument,
                         "orbit": self.orbit,
                         "year": self.year,
                         "month": self.month,
                         "day": self.day,
                         "hour": self.hour,
                         "minute": self.minute}

            self.identify_filetype()
            if self.filetype != '':
                message = self.create_message()            
                print "Publishing message %s" %str(message)
                self.pub.send(str(message))
                self.__clean__()    
    
    
    def process_IN_CLOSE_WRITE(self, event):
        """
        """
        self.logger.debug("new file created and closed %s" %event.pathname)
        #print event.__dict__
        # New file created and closed
        if not event.dir:
            self.parse_file_info(event)
            self.info = {"uri": self.fullname,
                         "satellite": self.satellite,
                         "satnumber": self.satnumber,
                         "instrument": self.instrument,
                         "orbit": self.orbit,
                         "year": self.year,
                         "month": self.month,
                         "day": self.day,
                         "hour": self.hour,
                         "minute": self.minute}

            self.identify_filetype()
            if self.filetype != '':
                message = self.create_message()            
                print "Publishing message foo %s" %str(message)
                self.pub.send(str(message))
                self.__clean__()    

                
    def identify_filetype(self):
        """
        """
        for filetype in self.filetypes:
            if fnmatch.fnmatch(self.filename, '*' + filetype + '*'):
                self.filetype = filetype
                break
        
    def create_message(self):
        """
        Create broadcasted message
        """
        return Message(self.subject, str(self.filetype), self.info)


    def parse_file_info(self, event):
        '''
        '''
        self.filename = event.name
        self.filepath = event.path
        self.fullname = event.pathname
        parts = event.name.split('.')[0].split('_')
        self.satellite = parts[1][:4]
        self.satnumber = parts[1][4:]
        self.year = int(parts[2][:4])
        self.month = int(parts[2][4:6])
        self.day = int(parts[2][6:])
        self.hour = int(parts[3][:2])
        self.minute = int(parts[3][2:])
        self.instrument = 'avhrr'
        self.orbit = parts[4]

    
if __name__ == "__main__":    
    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser() 
    
    parser.add_argument("-d", "--monitored_dirs", dest="monitored_dirs",
                        nargs='+',
                        type=str,
                        default='.',
                        help="Names of the monitored directories separated by space")

    parser.add_argument("-p", "--publish_port", dest="publish_port",
                      default=9000, type=int, 
                      help="Local port where messages are published")

    parser.add_argument("-t", "--filetypes", dest="filetypes",
                        type=str,
                        nargs='+',
                        default=[],
                        help="Identifier for monitored files")

    #parser.add_argument("-c", "--configuration_file", dest="configuration_file",
    #                  default='noaa15_products.xml', type=str, 
    #                  help="Name of the xml configuration file")


    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit()
    else:
        args = parser.parse_args()

    #Event handler observes the operations in defined folder   
    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE #IN_CREATE # monitored events
    
    #message_dict = {'publish_port':args.publish_port, 'filetypes':args.filetypes, 'subject':'/Joonas/'}
    
    event_handler = EventHandler(args.filetypes,
                                 publish_port = args.publish_port)
    notifier = Notifier(wm, event_handler)
    for monitored_dir in args.monitored_dirs:
        wdd = wm.add_watch(monitored_dir, mask, rec = True)
    
#    notifier.loop(daemonize=True,\
#                    pid_file='/tmp/pyinotify.pid',\
#                    stdout='/tmp/stdout.txt')

    notifier.loop()
