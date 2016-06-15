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

"""Prepare tle and satpos (and ephe) files for AAPP, using the tleing and
alleph scripts from AAPP

"""

import logging
from glob import glob
import os
from datetime import datetime
import shutil
from subprocess import Popen, PIPE

LOG = logging.getLogger(__name__)


def do_tleing(aapp_prefix, tle_in, tle_out, tle_call):
    """Get the tle-file and copy them to the AAPP data structure 
       and run the AAPP tleing script and executable"""

    infiles = glob("%s/tle-*" % (tle_in))
    copy_done = False
    for filename in infiles:
        name = os.path.basename(filename)
        try:
            dtobj = datetime.strptime(name, "tle-%Y%m%dT%H%M%S.txt")
        except ValueError:
            try:
                dtobj = datetime.strptime(name, "tle-%Y%m%d.txt")
            except ValueError:
                print("Skip file, " + str(filename))
                continue

        subdirname = dtobj.strftime('%Y_%m')
        outfile = "%s/%s/%s" % (tle_out, subdirname, name.replace('-', '_'))
        print "OUTPUT file = ", outfile

        subdir = "%s/%s" % (tle_out, subdirname)
        if not os.path.exists(subdir):
            os.mkdir(subdir)
        shutil.copy(filename, outfile)
        copy_done = True

    if copy_done:
        print "tle files have been found and copied. Do the tleing..."

        my_env = os.environ.copy()
        my_env['AAPP_PREFIX'] = aapp_prefix
        for key in my_env:
            LOG.debug("ENV: " + str(key) + ": " + str(my_env[key]))
        import shlex
        myargs = shlex.split(str(tle_call))
        LOG.debug('Command sequence= ' + str(myargs))
        proc = Popen(myargs, shell=False, env=my_env,
                     stderr=PIPE, stdout=PIPE)
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

    else:
        print "No tle-files copied. No tleing will be done..."

    return
