#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Martin Raspaud

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>
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

"""This is the minion for the dungeon keeper
"""

import os
import time
import logging
import logging.config
logger = logging.getLogger(__name__)

import socket
import fcntl
import struct

# from http://stackoverflow.com/questions/11735821/python-get-localhost-ip

def get_interface_ip(ifname):
    """Get ip of interface *ifname*
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(sock.fileno(), 0x8915,
                                        struct.pack('256s',
                                                    ifname[:15]))[20:24])

def get_lan_ip(interface=None):
    """Get ip on lan
    """
    if interface is None:
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "eth3",
            "eth4",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
    else:
        interfaces = [interface]
    for ifname in interfaces:
        try:
            ip_ = get_interface_ip(ifname)
            break
        except IOError:
            pass
    try:
        return ip_
    except UnboundLocalError:
        return socket.gethostbyname(socket.gethostname())

from threading import Thread, Event
from posttroll.publisher import NoisyPublisher, context
from posttroll.message import Message

class Heart(Thread):
    """Send heartbeats once in a while.

    *pub* is the publisher to use. If it's None, a new publisher
    will be created.
    *interval* is the interval to send heartbeat on, in seconds.
    *kwargs* is the things you want to send with the beats.
    """

    def __init__(self, pub, interval=30, **kwargs):
        Thread.__init__(self)
        self._loop = True
        self._event = Event()
        self._to_send = kwargs
        self._interval = interval
        if pub is not None:
            self._pub = pub
            self._stop_pub = False
        else:
            self._pub = NoisyPublisher("Heart", 0)
            self._pub.start()
            self._stop_pub = True

    def run(self):
        while self._loop:
            msg = Message("/heart/minion", "heartbeat", self._to_send).encode()
            self._pub.send(msg)
            self._event.wait(self._interval)

    def stop(self):
        """Cardiac arrest
        """
        self._loop = False
        if self._stop_pub:
            self._pub.stop()
        self._event.set()

import zmq

class CommandReceiver(object):
    """Receive commands from an higher entity.
    """
    def __init__(self):
        self._response = None
        self._response_port = None
        self._loop = False
        self.thr = None
        self._server = None

    def start(self):
        """Start the process.
        """
        self._server = context.socket(zmq.REP)
        self._response_port = self._server.bind_to_random_port("tcp://*")
        self._loop = True
        self.thr = Thread(target=self._loop_fun)
        self.thr.start()

    def stop(self):
        """Stop the process
        """
        self._loop = False
        self._server.setsockopt(zmq.LINGER, 1)
        self._server.close()

    def restart(self):
        """Restart the process.
        """
        logger.debug("restart requested")
        self.stop()
        self.start()

    def poke(self):
        """Say if we're alive
        """
        return self._loop

    def reload(self):
        """Reload config
        """
        logger.debug("reload requested")


    def status(self):
        """Send back the status of the process (running or not)
        """
        logger.debug("status requested")

    def _loop_fun(self):
        while self._loop:
            request = self._server.recv()
            try:
                getattr(self, request)()
            except Exception as e:
                self._server.send("failed: " + str(e))
            else:
                self._server.send("done")


class Minion(CommandReceiver):
    """A simple wrapper to include a heartbeat and a command receiver.
    """
    def __init__(self):
        CommandReceiver.__init__(self)
        logger.debug("init")
        self._heart = None

    def start(self):
        CommandReceiver.start(self)
        url = "tcp://" + str(get_lan_ip()) + ":" + str(self._response_port)
        self._heart = Heart(None, interval=1,
                            pid=os.getpid(),
                            url=url)
        self._heart.start()

    def stop(self):
        """Stop minion
        """
        self._heart.stop()
        CommandReceiver.stop(self)


if __name__ == '__main__':
    logging.config.fileConfig("../etc/logging.cfg")
    logger = logging.getLogger("minion")

    try:
        minion = Minion()
        minion.start()
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        logger.debug("Interrupted")
    except Exception as e:
        print e
        logger.exception("Something bad happened…")
    finally:
        minion.stop()
        logging.shutdown()
        time.sleep(0.5)
        context.term()
