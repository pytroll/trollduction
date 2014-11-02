#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Adam.Dybbroe

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

"""Make aqua messages for ingestion from receiver.log
"""

# cat /var/log/satellit/receiver.log | grep 66482 | grep "safe.smhi.se" > kurt

import sys
import os
import tempfile

if len(sys.argv) < 4:
    print("Usage: " +
          sys.argv[0] + " <log file> <orbit number> <server domain (eg safe.smhi.se)>")
    sys.exit(1)

logfile = sys.argv[1]
orbnum = sys.argv[2]
server = sys.argv[3]
outfile = tempfile.mktemp()

os.system('cat %s | grep %s | grep %s > %s' % (logfile,
                                               orbnum,
                                               server,
                                               outfile))
with open(outfile, 'r') as fd1:
    inlines = fd1.readlines()


newl = [
    '"""' + s.split('publishing')[-1].strip() + '""",\n' for s in inlines ]

fd2 = open('./aqua_messages.txt', 'w')
fd2.writelines(newl)
fd2.close()
