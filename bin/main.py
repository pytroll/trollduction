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


from trollduction.old_trollduction import OldTrollduction as Trollduction
import argparse
import logging
import logging.config

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file")
    parser.add_argument("-l", "--log-config",
                        help="log config file to use",
                        default="./etc/logging.cfg")

    args = parser.parse_args()

    logger = logging.getLogger("trollduction")
    logging.config.fileConfig(args.log_config)

    # Create a new Trollduction instance, initialised with the config
    td = Trollduction(args.config_file)
    # Run Trollduction
    try:
        td.run_single()
    except KeyboardInterrupt:
        logging.shutdown()

    print "Thank you for using pytroll/trollduction! See you soon on pytroll.org."
