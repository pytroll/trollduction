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

"""./trollstalker.py -d /tmp/data/new/ -p 9000 -m EPI
"""

import argparse
import logging, logging.handlers
from pyinotify import WatchManager, ThreadedNotifier, ProcessEvent
import pyinotify
import fnmatch
import sys
import time

from posttroll.publisher import NoisyPublisher
from posttroll.message import Message


class EventHandler(ProcessEvent):
    """
    Event handler class for inotify.
    """
    def __init__(self, filemasks, filetypes, publish_port=0):
        super(EventHandler, self).__init__()
        
        self.logger = logging.getLogger(__name__)
        self._pub = NoisyPublisher("trollstalker", publish_port, filetypes)
        self.pub = self._pub.start()
        self.filemasks = filemasks
        self.filename = ''
        self.info = {}
        self.filetype = ''
        #        self.subject = '/NewFileArrived'

    def stop(self):
        self._pub.stop()
        
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
            if self.filetype != '' and self.check_filemasks():
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
            # parse information and create self.info dict{}
            self.parse_file_info(event)
#            self.identify_filetype()
            if self.filetype != '' and self.check_filemasks():
                message = self.create_message()            
                print "Publishing message foo %s" %str(message)
                self.pub.send(str(message))
            self.__clean__()    

                
    def check_filemasks(self):
        """
        """
        for filemask in self.filemasks:
            if fnmatch.fnmatch(self.filename, '*' + filemask + '*'):
                return True
        return False
        
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

        if 'MSG' in self.filename:
            # MSG
            # H-000-MSG3__-MSG3________-HRV______-000001___-201402130515-__
            self.filetype = 'msg_xrit'
            self.satellite = 'meteosat'
            self.instrument = 'seviri'
            parts = self.filename.split('-')
            self.satnumber = str(int(parts[2].strip('_')[-1])+7)
            self.channel = parts[4].strip('_')
            self.segment = parts[5].strip('_')
            self.year = int(parts[6][:4])
            self.month = int(parts[6][4:6])
            self.day = int(parts[6][6:8])
            self.hour = int(parts[6][8:10])
            self.minute = int(parts[6][10:])
            self.orbit = ''
            if parts[7].strip('_') == 'C':
                self.compressed = 1
            else:
                self.compressed = 0

            self.subject =  "/" + self.filetype + '/NewFileArrived/'
            self.info = {"uri": self.fullname,
                         "satellite": self.satellite,
                         "satnumber": self.satnumber,
                         "instrument": self.instrument,
                         "orbit": self.orbit,
                         "year": self.year,
                         "month": self.month,
                         "day": self.day,
                         "hour": self.hour,
                         "minute": self.minute,
                         "segment": self.segment,
                         "channel": self.channel,
                         "compressed": self.compressed}

        elif 'hrpt' in self.filename and 'noaa' in self.filename and 'l1b' in self.filename:
            # HRPT NOAA l1b file
            #
            self.filetype = 'hrpt_noaa_l1b'
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

            self.subject = '/' + self.filetype + '/NewFileArrived/'
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


    
if __name__ == "__main__":    
    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser() 
    
    parser.add_argument("-d", "--monitored_dirs", dest="monitored_dirs",
                        nargs='+',
                        type=str,
                        default='.',
                        help="Names of the monitored directories separated by space")

    parser.add_argument("-p", "--publish_port", dest="publish_port",
                      default=0, type=int, 
                      help="Local port where messages are published")

    parser.add_argument("-m", "--filemask", dest="filemasks",
                        type=str,
                        nargs='+',
                        default=[],
                        help="Identifier for monitored files")

    parser.add_argument("-t", "--filetype", dest="filetypes",
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
    
    event_handler = EventHandler(args.filemasks, args.filetypes,
                                 publish_port=args.publish_port)
    notifier = ThreadedNotifier(wm, event_handler)
    for monitored_dir in args.monitored_dirs:
        wdd = wm.add_watch(monitored_dir, mask, rec = True)
    
        #    notifier.loop(daemonize=True,\
        #                    pid_file='/tmp/pyinotify.pid',\
        #                    stdout='/tmp/stdout.txt')

    notifier.start()
    try:
        while True:
            time.sleep(6000000)
    except KeyboardInterrupt:
        print "Interupting TrollStalker"
    finally:
        event_handler.stop()
        notifier.stop()
