#!/usr/bin/python

from posttroll.publisher import Publisher, get_own_ip
from posttroll.message import Message
import time

PORT = 5555
PUB_ADDRESS = "tcp://" + str(get_own_ip()) + ":%04d" % PORT
MSG_TYPE = 'type2'
INTERVAL = 5

def test_publisher():
    '''Simple publisher to test Listener class
    '''

    # Create new publisher instance
    pub = Publisher(PUB_ADDRESS)

    i = 0
    while True:
        message = Message('/test/message', MSG_TYPE, 'Message number %d' % i)
        print "Sent ", message
        pub.send(str(message))
        i += 1
        time.sleep(INTERVAL)


if __name__ == '__main__':
    '''Start publisher
    '''
    test_publisher()
