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

from tempfile import mkstemp
from trollduction.producer import Trollduction
import argparse
import logging
import logging.config
from ConfigParser import ConfigParser, NoOptionError
import signal
import sys
import os
import time


def create_instance_log_config(orig_log_config, process_num):
    '''
    Creates a copy of the log config file and replaces
    all occurencies of "%PROCNUM%" with the specified
    *process_num*. Can be used to ensure that multiple instances
    of l2processors write to own log files but share the same
    log config file
    '''
    _, temp_file = mkstemp()
    try:
        with open(orig_log_config) as infile:
            with open(temp_file, 'w') as outfile:
                replacements = {'%PROCNUM%': '{0:02d}'.format(process_num)}
                for line in infile:
                    for src, target in replacements.iteritems():
                        line = line.replace(src, target)
                    outfile.write(line)
    except:
        os.remove(temp_file)
        raise
    return temp_file


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", dest="config_file",
                        type=str,
                        default='',
                        help="The file containing configuration parameters.")
    parser.add_argument("-C", "--config_item", dest="config_item",
                        type=str,
                        default='',
                        help="The item in the file with configuration.")
    parser.add_argument("-N", "--process_num", dest="process_num",
                        type=int,
                        default=None,
                        help="the process number used to assign workload "
                        "from product configuration")

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

    return args


def setup_logging(config, config_item, process_num=None):
    """Setup logging"""
    try:
        log_config = config.get(config_item, "td_log_config")
        if 'template' in log_config:
            print "Template file given as Trollduction logging config," \
                " aborting!"
            sys.exit()

    except NoOptionError:
        logging.basicConfig()
    else:
        if process_num is None:
            logging.config.fileConfig(log_config,
                                      disable_existing_loggers=False)
        else:
            inst_log_config = create_instance_log_config(log_config,
                                                         process_num)
            logging.config.fileConfig(inst_log_config,
                                      disable_existing_loggers=False)
            if os.path.exists(inst_log_config):
                os.remove(inst_log_config)
    logging.debug("Logging setup completed.")


def main():
    """Main()"""

    args = parse_args()

    config = ConfigParser()
    config.read(args.config_file)

    setup_logging(config, args.config_item, args.process_num)

    logger = logging.getLogger("trollduction")

    # Create a new Trollduction instance, initialised with the config
    cfg = dict(config.items(args.config_item))
    cfg["config_item"] = args.config_item
    cfg["config_file"] = args.config_file
    cfg["process_num"] = args.process_num
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
        sys.exit()

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
        trd.shutdown()
        os._exit(os.EX_SOFTWARE)

    print "Thank you for using pytroll/l2processor!" \
        "See you soon on pytroll.org."

if __name__ == '__main__':
    main()
