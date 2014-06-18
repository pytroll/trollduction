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

"""Build images from l1 data.
./l2processor.py -c ../examples/master_config.ini -C noaa_hrpt
"""

from trollduction.trollduction import Trollduction
import argparse
import logging
import logging.config
from ConfigParser import ConfigParser, NoOptionError
import signal

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file",
                        help="The file containing configuration parameters.")
    parser.add_argument("config_item",
                        help="The item in the file with configuration.")

    args = parser.parse_args()

    config = ConfigParser()
    config.read(args.config_file)

    try:
        log_config = config.get(args.config_item, "td_log_config")
    except NoOptionError:
        logging.basicConfig()
    else:
        logging.config.fileConfig(log_config)

    logger = logging.getLogger("trollduction")


    # Create a new Trollduction instance, initialised with the config
    cfg = dict(config.items(args.config_item))
    cfg["config_item"] = args.config_item
    cfg["config_file"] = args.config_file
    td = Trollduction(cfg)

    def shutdown(*args):
        del args
        td.shutdown()
        logging.shutdown()

    signal.signal(signal.SIGTERM, shutdown)

    # Run Trollduction
    try:
        td.run_single()
    except KeyboardInterrupt:
        logging.shutdown()

    print "Thank you for using pytroll/l2processor! See you soon on pytroll.org."
