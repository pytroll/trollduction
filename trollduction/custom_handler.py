#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Martin Raspaud

# Author(s):

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

"""For Panu
"""

from logging.handlers import TimedRotatingFileHandler
import re
import time
import os

KEYS = {"%Y": r"\d{4}",
        "%y": r"\d{2}",
        "%m": r"\d{2}",
        "%d": r"\d{2}",
        "%H": r"\d{2}",
        "%M": r"\d{2}",
        "%S": r"\d{2}",
        "%j": r"\d{3}"}

class PanusTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Like TimedRotatingFileHandler with a custom filename template.
    """

    def __init__(self, template, *args, **kwargs):

        self.template = template
        current_time = int(time.time())
        if kwargs.get("utc", False):
            time_tuple = time.gmtime(current_time)
        else:
            time_tuple = time.localtime(current_time)
        filename = time.strftime(self.template, time_tuple)

        self.match = os.path.basename(self.template)
        for key, val in KEYS.iteritems():
            self.match = self.match.replace(key, val)

        self.match = re.compile(self.match)
        TimedRotatingFileHandler.__init__(self, filename, *args, **kwargs)

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which assumed the date to be a
        suffix.
        """
        dirname, basename = os.path.split(self.baseFilename)
        del basename
        filenames = os.listdir(dirname)
        result = []
        for filename in filenames:
            if self.match.match(filename):
                result.append(os.path.join(dirname, filename))
        result.sort(reverse=True)
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        """
        do a rollover; If there is a backup count, then we have to get a list of
        matching filenames, sort them and remove the oldest ones.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        now = time.localtime(current_time)[-1]
        if self.utc:
            time_tuple = time.gmtime(current_time)
        else:
            time_tuple = time.localtime(current_time)
        self.baseFilename = time.strftime(self.template, time_tuple)
        if self.backupCount > 0:
            for old_file in self.getFilesToDelete():
                os.remove(old_file)
        self.stream = self._open()
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.

        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and \
                not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if now != dst_at_rollover:
                # DST kicks in before next rollover,
                # so we need to deduct an hour
                if not now:
                    addend = -3600
                # DST bows out before next rollover,
                # so we need to add an hour
                else:
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at


