#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c14526.ad.smhi.se>

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

"""Posttroll runner for OSISAF SST post-processing
"""
import os
import ConfigParser

import logging
LOG = logging.getLogger(__name__)

CONFIG_PATH = os.environ.get('SSTRUNNER_CONFIG_DIR', './')

CONF = ConfigParser.ConfigParser()
CONF.read(os.path.join(CONFIG_PATH, "osisaf_sst_config.cfg"))

MODE = os.getenv("SMHI_MODE")
if MODE is None:
    MODE = "offline"

OPTIONS = {}
for option, value in CONF.items(MODE, raw=True):
    OPTIONS[option] = value

SST_OUTPUT_DIR = OPTIONS['sst_outdir']

servername = None
import socket
servername = socket.gethostname()
SERVERNAME = OPTIONS.get('servername', servername)


#: Default time format
_DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

#: Default log format
_DEFAULT_LOG_FORMAT = '[%(levelname)s: %(asctime)s : %(name)s] %(message)s'


import sys
from glob import glob
from urlparse import urlparse
import posttroll.subscriber
from posttroll.publisher import Publish
from posttroll.message import Message

from datetime import datetime, timedelta


class SstRunError(Exception):
    pass


def start_sst_processing(sst_file,
                         mypublisher, message):
    """From a posttroll message start the modis lvl1 processing"""

    LOG.info("")
    LOG.info("sst-file dict: " + str(sst_file))
    LOG.info("\tMessage:")
    LOG.info(message)
    urlobj = urlparse(message.data['uri'])
    LOG.info("Server = " + str(urlobj.netloc))
    if urlobj.netloc != SERVERNAME:
        return sst_file
    LOG.info("Ok... " + str(urlobj.netloc))
    LOG.info("Sat and Instrument: " + str(message.data['platform_name']) + " "
             + str(message.data['sensor']))

    if 'start_time' in message.data:
        start_time = message.data['start_time']
        scene_id = start_time.strftime('%Y%m%d%H%M')
    else:
        LOG.warning("No start time in message!")
        start_time = None
        return sst_file

    if 'end_time' in message.data:
        end_time = message.data['end_time']
    else:
        LOG.warning("No end time in message!")
        end_time = None

    if (message.data['platform_name'] in ['Suomi-NPP', ] and
            message.data['instruments'] == 'viirs'):

        path, fname = os.path.split(urlobj.path)
        LOG.debug("path " + str(path) + " filename = " + str(fname))

        sst_file[scene_id] = os.path.join(path, fname)

    LOG.debug("...that was it :-)")

    return sst_file


def sst_live_runner():
    """Listens and triggers processing"""

    LOG.info("*** Start the OSISAF SST post-processing runner:")
    with posttroll.subscriber.Subscribe('', ['OSISAF/GHRSST', ], True) as subscr:
        with Publish('sst_runner', 0) as publisher:
            sstfile = {}
            for msg in subscr.recv():
                sstfile = start_sst_processing(sstfile,
                                               publisher, msg)


if __name__ == "__main__":

    handler = logging.StreamHandler(sys.stderr)

    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt=_DEFAULT_LOG_FORMAT,
                                  datefmt=_DEFAULT_TIME_FORMAT)
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(logging.DEBUG)
    logging.getLogger('posttroll').setLevel(logging.INFO)

    LOG = logging.getLogger('sst_runner')

    sst_live_runner()
