#!/usr/bin/python

from posttroll.subscriber import Subscriber
from multiprocessing import Pipe
from collections import deque
from threading import Thread

class Listener(object):
    '''PyTroll listener class using Posttroll for receiving messages
    '''

    def __init__(self, ip=None, port=None, child_pipe=None, deque_length=None):
        '''Object members
        '''
        self.address_list = []
        self.type_list = []
        self.add_address(ip, port)
        self.deque = deque(maxlen=deque_length)
        self.pipe = child_pipe
        
    def add_address(self, ip, port):
        '''Add address+port combination to listen for messages
        '''
        if ip is not None and port is not None:
            self.address_list.append('tcp://'+ip+':%04d' % port)

    def add_address_list(self, address_list):
        '''Add a list of addresses to listen for messages
        '''
        for address in address_list:
            self.address_list.append(address)

    def create_subscriber(self):
        '''Create a new subscriber object using existing address and
        type configurations
        '''
        if len(self.address_list) > 0:
            if len(self.type_list) > 0:
                self.subscriber = Subscriber(self.address_list, 
                                             *self.type_list)
            else:
                print "No message types defined!"
                # raise error 'No message types defined'
        else:
            print "No message publishers defined!"
            # raise error 'No message publishers defined'

    def send_to_pipe(self, msg):
        '''Send the received message to parent via a Pipe
        '''
        self.pipe.send(msg)

    def start(self):
        '''Start listening
        '''
        print "Start listening for messages"

        for msg in self.subscriber.recv():
            print "New message received"
            # If there is no Pipe, store the message to a deque list
            if self.pipe is None:
                self.deque.append(msg)
            else:
                # Send the messages in deque before sending new messages
                while len(self.deque) > 0:
                    self.send_to_pipe(self.deque.popleft())
            self.send_to_pipe(msg)


if __name__ == "__main__":
    '''Example main for Listener
    '''

    import sys
    from posttroll.publisher import get_own_ip

    # Two sources for incoming messages
    OWN_PORT = 5555
    OWN_ADDRESS = str(get_own_ip())

    EXTERNAL_PORT = 9000
    EXTERNAL_ADDRESS = "192.168.0.100"

    # Listen to two types of messages
    message_types = ["type1", "type2"]

    # Create a Pipe to get messages from the Listener
    parent_conn, child_conn = Pipe()

    # Init Listener
    listener = Listener(child_pipe=child_conn)
    listener.add_address(OWN_ADDRESS, OWN_PORT)
#    listener.add_address(EXTERNAL_ADDRESS, EXTERNAL_PORT)
    listener.type_list = message_types
    listener.create_subscriber()

    # Start the listener to a new Thread
    proc = Thread(target=listener.start)
    # Make the Thread daemonic, so it'll exit when the main() is closed
    proc.setDaemon(True)
    proc.start()

    # Read the messages and do something with them
    while True:
        try:
            msg = parent_conn.recv()
            print msg
        except:
            proc.join(1)
            sys.exit()
