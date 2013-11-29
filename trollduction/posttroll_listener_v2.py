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


from posttroll.publisher import Publisher, get_own_ip
from posttroll.subscriber import Subscriber
from posttroll.message import Message
from multiprocessing import Pool
from multiprocessing import Pipe
from collections import deque
from mpop.utils import debug_on
debug_on()
#from multiprocessing import Process

from threading import Thread as Process

import time

OWN_PORT = 9000
OWN_ADDRESS = str(get_own_ip())
#OWN_ADDRESS = str("127.0.0.1")

JOONAS_PORT = 9000
JOONAS_ADDRESS = "10.240.23.37"


class Listener(object):

    '''PyTroll listener class for reading messages and adding them to
    deque
    '''

    def __init__(self, ip=None, port=None, processes=2, pipe=None):
        '''
        '''
        self.address_list = []
        self.type_list = []
        self.add_address(ip, port)
        self.deque = deque()
        self.pipe = pipe
        self.create_subscriber()
        
    def add_address(self, ip, port):
        '''
        '''
        if ip is not None and port is not None:
            self.address_list.append('tcp://'+ip+':%05d' % port)

    def add_address_list(self, address_list):
        '''
        '''
        for address in address_list:
            self.address_list.append(address)

    def create_subscriber(self):
        '''
        '''
        if len(self.address_list) > 0:
            self.subscriber = Subscriber(self.address_list, 
                                         self.type_list)

    def send_to_pipe(self, msg):
        '''
        '''
        self.pipe.send(msg)

    def start(self):
        '''
        '''

        print "start"


        for msg in self.subscriber.recv():
            print "new msg"
            if self.pipe is None:
                self.deque.append(msg)
            else:
                while len(self.deque) > 0:
                    self.send_to_pipe(self.deque.popleft())
            self.send_to_pipe(msg)

        #i = 0
        #while True:
        #    self.send_to_pipe(i)
        #    i += 1
        #    time.sleep(2)

def printer(msg):
    print msg

def do_processing(msg):
    from xml_read import read_product_file
    pl, mda = read_product_file('/local_disk/usr/src/mpop-smhi.old/etc/noaa15_products.xml')

    prods = pl["euron1"]

    info = msg.data

    from mpop.satellites import GenericFactory
    from datetime import datetime
    g = GenericFactory.create_scene(str(info["satellite"]), str(info["number"]), str(info["instrument"]), datetime.utcnow(), None)

    g.load(get_prerequisites(g.image, prods.keys()))
    for prod, files in prods.items():
        img = getattr(g.image, prod)()
        print "saving", img, "to", files

def get_prerequisites(obj, products):
    prereqs = set()
    for prod in products:
        prereqs |= getattr(obj, prod).prerequisites
    return prereqs


if __name__ == "__main__":

    parent_conn, child_conn = Pipe()

    listener = Listener(pipe=child_conn)
    print "subscribing to ", OWN_ADDRESS, OWN_PORT
    listener.add_address(OWN_ADDRESS, OWN_PORT)
    #print "subscribing to ", JOONAS_ADDRESS, JOONAS_PORT
    #listener.add_address(JOONAS_ADDRESS, JOONAS_PORT)
    #listener.type_list = ["type1", "NOAA19*.hmf"]
    listener.type_list = ["hmf"]
    #listener.type_list = []
    listener.create_subscriber()

    proc = Process(target=listener.start)
    proc.start()

    pool = Pool(processes=2)
    while True:
        msg = parent_conn.recv()
        #pool.apply_async(do_processing, args=(msg,))
        pool.apply_async(printer, args=(msg,))
        do_processing(msg)

        # Send reply that the message was received
        #publisher.send_ack(msg)
        #print msg
#        time.sleep(1)



"""
from posttroll.publisher import Publish
from posttroll.message import Message
import time

try:
    with Publish("my_module", ["hmf"], 9000) as pub:
        counter = 0
        while True:
            counter += 1
            message = Message("/NewFileArrived/", "hmf", str(counter))
            print "publishing", message
            pub.send(str(message))
            time.sleep(3)
except KeyboardInterrupt:
    print "terminating publisher..."



from posttroll.publisher import Publisher, get_own_ip
from posttroll.message import Message
import time

PUB_ADDRESS = "tcp://" + str(get_own_ip()) + ":9000"
PUB = Publisher(PUB_ADDRESS)

try:
    counter = 0
    while True:
        counter += 1
        print "publishing " + str(counter)
        message = Message("/NewFileArrived/", "hmf", str(counter))
        PUB.send(str(message))
        time.sleep(3)
except KeyboardInterrupt:
    print "terminating publisher..."
    PUB.stop()
    
"""
