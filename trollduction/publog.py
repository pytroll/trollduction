# -*- coding: utf-8 -*-

# Copyright (c) 2014

# Author(s):

#   Panu Lahtinen <panu.lahtinen@fmi.fi>

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

'''Logger and publisher classes for Trollduction
'''

import logging
from posttroll.publisher import NoisyPublisher
from posttroll.message import Message
import os
import datetime as dt
from threading import Thread
import time

class PubLog(object):
    '''Class to hold logger and message publisher instances
    '''
    def __init__(self, log_dir=None, fname=None, name=None,
                 file_log_level=None, console_log_level=None):
        self.logger = Logger(log_dir, fname, name, 
                             file_log_level, console_log_level)
        self.publisher = Publisher(name)

        self.running = False
        self.hb_thread = Thread(target=self.heartbeat)
        self.hb_thread.setDaemon(True)
        self.hb_thread.start()


    def publish_and_log(self, level='info', info='', msg=True, log=True):
        '''Publish and/or log the given information text.
        '''
        
        # Log the information
        if log and self.logger is not None:
            if level.lower() == 'heartbeat':
                logger = getattr(self.logger.logger, 'debug')
            else:
                logger = getattr(self.logger.logger, level)
            logger(info)

        # Publish a message using Posttroll
        if msg and self.publisher is not None:
            self.publisher.send(info, level)


    def heartbeat(self):
        '''Send heartbeat messages every 60 seconds
        '''
        
        self.running = True
        i = 0
        while True:
            if self.running:
                if i > 59:
                    self.publish_and_log(info='Still alive', level='heartbeat')
                    i = 0
            else:
                break
            time.sleep(1)
            i += 1


    def stop(self):
        '''Stop logger and publisher instances
        '''
        self.running = False
        self.hb_thread.join()
        self.publisher.stop()

class Logger(object):
    '''File and console logger for Trollduction
    '''
    def __init__(self, log_dir=None, fname_template=None, name=None, 
                 file_log_level='INFO', console_log_level='INFO'):

        self.log_dir = log_dir
        self.fname_template = fname_template
        self.name = name
        self.file_log_level = file_log_level
        self.console_log_level = console_log_level
        self.full_fname = None
        self.logger = None

        self.check_logger()


    def check_logger(self):
        '''Check if date has changed and the file logger needs to be
        updated.
        '''

        fname = os.path.join(self.log_dir, self.fname_template)
        utc_date = dt.datetime.utcnow()
        fname = utc_date.strftime(fname)
        self.full_fname = fname

        # Create log directory, if necessary
        if len(self.log_dir) and not os.path.isdir(self.log_dir):
            os.makedirs(self.log_dir)

        # Do nothing, if the log file already exists and logger has been set
        if os.path.exists(fname) and self.logger is not None:
            return
        # Set logger with new date and stuff
        else:
            self.set_logger()


    def set_logger(self):
        '''Create a logger
        '''

        if self.logger is not None:
            # Close and remove old file handlers, if any
            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)

        # Create a new logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        # Log message format
        formatter = logging.Formatter('[%(levelname)s: %(asctime)s : '
                                      '%(name)s] %(message)s')

        # Create file handler
        filehandler = logging.FileHandler(self.full_fname)
        # Set logging level
        try:
            log_level = getattr(logging, self.file_log_level)
        except KeyError:
            log_level = logging.INFO
        filehandler.setLevel(log_level)
        filehandler.setFormatter(formatter)
                
        # Attach file handler
        self.logger.addHandler(filehandler)

        # Create console logger
        consolehandler = logging.StreamHandler()
        # Set logging level
        try:
            log_level = getattr(logging, self.console_log_level)
        except KeyError:
            log_level = logging.INFO
        consolehandler.setLevel(log_level)

        consolehandler.setFormatter(formatter)
        self.logger.addHandler(consolehandler)

        # Log the logger startup
        self.logger.info('Logger loaded')
        

class Publisher(object):
    '''Message publisher for Trollduction.
    '''
    def __init__(self, name, publish_port=0):
        self.subject = '/%s/Message/' % (name)
        self.name = name
        self.msg_type = name+'_message' # eg. HRPT_l1b_message
        #self._pub = NoisyPublisher(self.msg_type, publish_port, self.msg_type)
        self._pub = NoisyPublisher(self.name, publish_port, self.name)
        self.pub = self._pub.start()


    def send(self, msg=None, level='info'):
        '''Send message
        '''
        message = Message(self.subject+level.upper()+'/', 
                          #str(self.msg_type), 
                          str(self.name), 
                          msg)
        #print message
        self.pub.send(str(message))

    def stop(self):
        '''Stop Publisher.
        '''
        self._pub.stop()
