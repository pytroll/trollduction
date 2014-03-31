#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2012, 2013, 2014 Martin Raspaud

# Author(s):

#   Panu Lahtinen  <panu.lahtinen@fmi.fi>
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

"""Trollduction entry point.
"""


from trollduction.trollduction import Trollduction, read_config_file
import argparse
import logging
from posttroll.logger import PytrollFormatter, PytrollHandler
import os.path
import time

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file")
    parser.add_argument("-v", "--verbose",
                        help="Print out debug messages also.",
                        action="store_true")

    args = parser.parse_args()

    td_config = read_config_file(args.config_file)

    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.DEBUG)

    utc = "use_local_time" not in td_config
    logging.Formatter.converter = time.gmtime

    formatter = logging.Formatter('[%(levelname)s: %(asctime)s : '
                                  '%(name)s] %(message)s')

    # Console logging

    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = getattr(logging, td_config.get('console_log_level', 'INFO'))

    console = logging.StreamHandler()

    console.setFormatter(formatter)
    console.setLevel(loglevel)
    root_logger.addHandler(console)

    if 'log_filename' in td_config:
        log_file = os.path.join(td_config.get('log_dir', '/tmp'),
                                td_config["log_filename"])
        filelogger = logging.handlers.TimedRotatingFileHandler(log_file,
                                                               when="midnight",
                                                               backupCount=7,
                                                               utc=utc)
        if args.verbose:
            loglevel = logging.DEBUG
        else:
            loglevel = getattr(logging, td_config.get('file_log_level', 'INFO'))

        filelogger.setFormatter(formatter)
        filelogger.setLevel(loglevel)
        root_logger.addHandler(filelogger)


    loglevel = logging.DEBUG

    nethandler = PytrollHandler("pytroll_logger")

    nethandler.setFormatter(PytrollFormatter('/%s/Message/' %
                                             (td_config["name"])))
    nethandler.setLevel(loglevel)
    root_logger.addHandler(nethandler)

    logger = logging.getLogger("trollduction")


    # Create a new Trollduction instance, initialised with the config
    td = Trollduction(args.config_file)
    # Run Trollduction
    try:
        td.run_single()
    except KeyboardInterrupt:
        nethandler.close()

    print "Thank you for using pytroll/trollduction! See you soon on pytroll.org."
