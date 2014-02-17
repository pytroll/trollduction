#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014

# Author(s):

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

from posttroll.subscriber import NSSubscriber
from posttroll.message import Message
from collections import deque
import logging

logger = logging.getLogger(__name__)

class Listener(object):
    '''PyTroll listener class for reading messages for Trollduction
    '''

    def __init__(self, data_type_list=None, pipe=None):
        '''Init Listener object
        '''
        self.data_type_list = data_type_list
        self.deque = deque()
        self.pipe = pipe
        self.subscriber = None
        self.create_subscriber()
        self.running = False
        

    def create_subscriber(self):
        '''Create a subscriber instance using specified addresses and
        message types.
        '''
        if self.subscriber is None:
            if len(self.data_type_list) > 0:
                self.subscriber = NSSubscriber(self.data_type_list,
                                               addr_listener=True)
                self.recv = self.subscriber.start().recv


    def send_to_pipe(self, msg):
        '''Send message to parent via a Pipe()
        '''
        self.pipe.send(msg)


    def run(self):
        '''Run listener
        '''

        logger.debug("Starting Listener")

        self.running = True

        for msg in self.recv(1):
            if msg is None:
                if self.running:
                    continue
                else:
                    break
            logger.debug("New message received")
            if self.pipe is None:
                self.deque.append(msg)
            else:
                while len(self.deque) > 0:
                    self.send_to_pipe(self.deque.popleft())
            self.send_to_pipe(msg)
            

    def stop(self):
        '''Stop subscriber and delete the instance
        '''
        
        self.running = False
        self.subscriber.stop()
        self.subscriber = None


    def restart(self):
        '''Restart subscriber
        '''
        self.stop()
        self.create_subscriber()
        self.run()
