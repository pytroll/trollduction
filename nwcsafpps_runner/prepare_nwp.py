#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c20671.ad.smhi.se>

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

"""Prepare NWP data for PPS
"""

import logging
from glob import glob
import os
from datetime import datetime
import ConfigParser
import tempfile
from subprocess import Popen, PIPE

LOG = logging.getLogger(__name__)

CONFIG_PATH = os.environ.get('PPSRUNNER_CONFIG_DIR', './')
CONF = ConfigParser.ConfigParser()
CONF.read(os.path.join(CONFIG_PATH, "pps_config.cfg"))

MODE = os.getenv("SMHI_MODE")
if MODE is None:
    MODE = "offline"


OPTIONS = {}
for option, value in CONF.items(MODE, raw=True):
    OPTIONS[option] = value


nhsp_path = OPTIONS.get('nhsp_path', None)
nhsp_prefix = OPTIONS.get('nhsp_prefix', None)
nhsf_path = OPTIONS.get('nhsf_path', None)
nhsf_prefix = OPTIONS.get('nhsf_prefix', None)
nwp_outdir = OPTIONS.get('nwp_outdir', None)
nwp_lsmz_filename = OPTIONS.get('nwp_static_surface', None)
nwp_output_prefix = OPTIONS.get('nwp_output_prefix', None)


def run_command(cmdstr):
    """Run system command"""

    import shlex
    myargs = shlex.split(str(cmdstr))

    LOG.debug("Command: " + str(cmdstr))
    LOG.debug('Command sequence= ' + str(myargs))
    proc = Popen(myargs, shell=False, stderr=PIPE, stdout=PIPE)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        LOG.info(line)

    while True:
        errline = proc.stderr.readline()
        if not errline:
            break
        LOG.info(errline)

    proc.poll()


def update_nwp(starttime, nlengths):
    """Prepare NWP grib files for PPS.  Consider only analysis times newer than
    *starttime*. And consider only the forecast lead times in hours given by
    the list *nlengths* of integers

    """

    tempfile.tempdir = nwp_outdir

    filelist = glob(os.path.join(nhsf_path, nhsf_prefix + "*"))
    if len(filelist) == 0:
        LOG.info("No input files! dir = " + str(nhsf_path))
        return

    LOG.debug('Files = ' + str(filelist))
    for filename in filelist:
        timeinfo = filename.rsplit("_", 1)[-1]
        timestamp, step = timeinfo.split("+")
        analysis_time = datetime.strptime(timestamp, '%Y%m%d%H%M')
        if analysis_time < starttime:
            continue
        if int(step[:3]) not in nlengths:
            continue

        LOG.info("timestamp, step: " + str(timestamp) + ' ' + str(step))
        result_file = os.path.join(
            nwp_outdir, nwp_output_prefix + timestamp + "+" + step)
        if os.path.exists(result_file):
            LOG.info("File: " + str(result_file) + " already there...")
            continue

        tmp_file = os.path.join(nwp_outdir, "tmp." + timestamp + "+" + step)
        LOG.info("result and tmp files: " +
                 str(result_file) + " " + str(tmp_file))
        cmd = ("grib_copy -w gridType=regular_ll " +
               os.path.join(nhsp_path, nhsp_prefix + timeinfo) + " " + tmp_file)
        run_command(cmd)

        tmpresult = tempfile.mktemp()
        cmd = ('cat ' + tmp_file + " " +
               os.path.join(nhsf_path, nhsf_prefix + timeinfo) +
               " " + nwp_lsmz_filename + " > " + tmpresult)
        os.system(cmd)
        os.remove(tmp_file)
        os.rename(tmpresult, result_file)

    return


if __name__ == "__main__":

    #: Default time format
    _DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    #: Default log format
    _DEFAULT_LOG_FORMAT = '[%(levelname)s: %(asctime)s : %(name)s] %(message)s'

    import sys
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt=_DEFAULT_LOG_FORMAT,
                                  datefmt=_DEFAULT_TIME_FORMAT)
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(logging.DEBUG)
    logging.getLogger('posttroll').setLevel(logging.INFO)

    LOG = logging.getLogger('test_update_nwp')

    from datetime import timedelta
    now = datetime.utcnow()
    update_nwp(now - timedelta(days=1), [9])
