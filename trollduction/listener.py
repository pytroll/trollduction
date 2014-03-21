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

'''Listener module for Trollduction.'''

from posttroll.subscriber import NSSubscriber
from collections import deque
import logging
from multiprocessing import Pipe
from threading import Thread

LOG = logging.getLogger(__name__)

class ListenerContainer(object):
    '''Container for listener instance
    '''
    def __init__(self, data_type_list=None):
        self.listener = None
        self.parent_conn = None
        self.child_conn = None
        self.thread = None

        if data_type_list is not None:
            # Create Pipe connection
            self.parent_conn, self.child_conn = Pipe()

            # Create a Listener instance
            self.listener = Listener(data_type_list=data_type_list, 
                                     pipe=self.child_conn)
            # Start Listener instance into a new daemonized thread.
            self.thread = Thread(target=self.listener.run)
            self.thread.setDaemon(True)
            self.thread.start()


    def restart_listener(self, data_type_list):
        '''Restart listener after configuration update.
        '''
        if self.listener is not None:
            if self.listener.running:
                self.stop()
        self.__init__(data_type_list=data_type_list)


    def stop(self):
        '''Stop listener.'''
        self.listener.stop()
        self.thread.join()
        self.parent_conn = None
        self.child_conn = None
        self.thread = None


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
        self.recv = None
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

        LOG.debug("Starting Listener")

        self.running = True

        for msg in self.recv(1):
            if msg is None:
                if self.running:
                    continue
                else:
                    break
            LOG.debug("New message received")
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
