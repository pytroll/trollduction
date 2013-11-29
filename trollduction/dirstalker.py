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

"""Looking at directories and sending messages.

Example message:
pytroll://oper/polar/direct_readout/norrköping file safuser@lxserv263.smhi.se 2013-11-29T01:25:16.803170 v1.01 application/json {"satellite": "NOAA 19", "format": "HRPT", "start_time": "2013-11-29T01:09:18", "level": "0", "orbit_number": 24775, "uri": "ssh://nimbus.smhi.se/archive/hrpt/20131129010918_NOAA_19.hmf", "filename": "20131129010918_NOAA_19.hmf", "instrument": ["avhrr/3", "mhs", "amsu"], "end_time": "2013-11-29T01:25:12", "type": "binary"}


"""


import argparse
import logging, logging.handlers
from pyinotify import WatchManager, Notifier, ProcessEvent
import pyinotify
import fnmatch
import sys
from datetime import datetime

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
        self.subject = '/NewFileArrived/'
        
    def __clean__(self):
        self.filename = ''
        self.filetype = ''
    
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
            self.filename = event.name
            self.info = {"uri": self.filename,
                         "satellite": "noaa",
                         "number": "19",
                         "instrument": "avhrr",
                         "start_time": datetime(2010, 2, 24, 11, 29),
                         "orbit": 5402}
            self.identify_filetype()
            if self.filetype != '':
                message = self.create_message()            
                print "Publishing message %s" %str(message)
                self.pub.send(str(message))
                self.__clean__()    
    
    
    def process_IN_CLOSE_WRITE(self, event):
        """
        """
                
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
    mask = pyinotify.IN_CREATE # monitored events
    
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
