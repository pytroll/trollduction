
from posttroll.subscriber import Subscriber
from posttroll.message import Message
from threading import Thread
#from collections import deque


class Listener(object):
    '''PyTroll listener class for reading messages for Trollduction
    '''

    def __init__(self, address_list=None, msg_type_list=None,
                 ip=None, port=None, pipe=None):
        '''Init Listener object
        '''
        self.address_list = address_list
        self.add_address_list(address_list)
        self.msg_type_list = []
        self.add_address(ip, port)
        #self.deque = deque()
        self.pipe = pipe
        self.create_subscriber()


    def add_address(self, ip, port):
        '''Add address that will be listened
        '''
        if ip is not None and port is not None:
            self.address_list.append('tcp://'+ip+':%04d' % port)


    def add_address_list(self, address_list):
        '''Add a list of addresses that will be listened
        '''
        for address in address_list:
            self.address_list.append(address)


    def create_subscriber(self):
        '''Create a subscriber instance using specified addresses and
        message types.
        '''
        if len(self.address_list) > 0:
            if len(self.msg_type_list) > 0:
                self.subscriber = Subscriber(self.address_list, 
                                             *self.msg_type_list)

    def send_to_pipe(self, msg):
        '''Send message to parent via a Pipe()
        '''
        self.pipe.send(msg)


    def start(self):
        '''Start listener
        '''

        print "Starting Listener"

        for msg in self.subscriber.recv():
            print "new msg"
            if self.pipe is None:
                self.deque.append(msg)
            else:
                while len(self.deque) > 0:
                    self.send_to_pipe(self.deque.popleft())
            self.send_to_pipe(msg)

