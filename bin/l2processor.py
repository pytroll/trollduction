#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015 Martin Raspaud

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

"""Build images from l1 data.
./l2processor.py -c /path/to/master_config.ini -C noaa_hrpt
"""

from trollduction.producer import Trollduction
import argparse
import logging
import logging.config
from ConfigParser import ConfigParser, NoOptionError
import signal
import sys
import os
import time

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", dest="config_file",
                        type=str,
                        default='',
                        help="The file containing configuration parameters.")
    parser.add_argument("-C", "--config_item", dest="config_item",
                        type=str,
                        default='',
                        help="The item in the file with configuration.")

    args = parser.parse_args()

    if args.config_file == '':
        print "Configuration file required! Use command-line switch -c <file>"
        sys.exit()
    if args.config_item == '':
        print "Configuration item required! Use command-line switch -C <item>"
        sys.exit()

    if 'template' in args.config_file:
        print "Template file given as master config, aborting!"
        sys.exit()

    config = ConfigParser()
    config.read(args.config_file)

    try:
        log_config = config.get(args.config_item, "td_log_config")
        if 'template' in log_config:
            print "Template file given as Trollduction logging config," \
                " aborting!"
            sys.exit()

    except NoOptionError:
        logging.basicConfig()
    else:
        logging.config.fileConfig(log_config)

    logger = logging.getLogger("trollduction")

    # Create a new Trollduction instance, initialised with the config
    cfg = dict(config.items(args.config_item))
    cfg["config_item"] = args.config_item
    cfg["config_file"] = args.config_file
    if "timezone" in cfg:
        print "Setting timezone to %s" % cfg["timezone"]
        os.environ["TZ"] = cfg["timezone"]
        time.tzset()
    else:
        print "No timezone given, defaulting to UTC timezone."
        os.environ["TZ"] = "UTC"
        time.tzset()

    if "template" in cfg["product_config_file"]:
        print "Template file given as trollstalker product config, " \
            "aborting!"

    trd = Trollduction(cfg)

    def shutdown(*args):
        logger.info("l2processor shutting down")
        del args
        trd.shutdown()
        logging.shutdown()

    signal.signal(signal.SIGTERM, shutdown)

    # Run Trollduction
    try:
        trd.run_single()
    except KeyboardInterrupt:
        logging.shutdown()
    except:
        logger.exception("Trollduction died!")

    print "Thank you for using pytroll/l2processor!" \
        "See you soon on pytroll.org."
