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

"""AAPP Level-1 processing on NOAA and Metop HRPT Direct Readout data. Listens
for pytroll messages from Nimbus (NOAA/Metop file dispatch) and triggers
processing on direct readout HRPT level 0 files (full swaths - no granules at
the moment)
"""

import os
import sys
LVL0_DATA_HOME = os.environ.get("LVL0_DATA_HOME", '')
DATA_ROOT_DIR = os.environ.get("DATA_ROOT_DIR", '')
PPS_DATA_HOME = os.environ.get("PPS_DATA_HOME", '')
AAPP_BIN_HOME = os.environ.get("AAPP_BIN_HOME", './')
AAPP_IN_DATDIR = os.environ.get("AAPP_IN_DATDIR", '')
WORKING_DIR = os.environ.get("WRK", './')  # AAPP Run dir

#SUPPORTED_NOAA_SATELLITES = os.environ.get("SUPPORTED_NOAA_SATELLITES", '')

NOAA_RUN_SCRIPT = "%s/smhi/AAPP_RUN_NOAA_WITH_ANA" % AAPP_BIN_HOME
METOP_RUN_SCRIPT = "%s/smhi/AAPP_RUN_METOP_SMHI" % AAPP_BIN_HOME

import ConfigParser

CONFIG_PATH = os.environ.get('AAPP_CONFIG_DIR', '')

AAPP_WORKDIR = os.environ.get("AAPP_WORKDIR", '')

CONF = ConfigParser.ConfigParser()
CONF.read(os.path.join(CONFIG_PATH, "aapp_config.cfg"))

MODE = os.getenv("SMHI_MODE")
if MODE is None:
    MODE = "offline"


OPTIONS = {}
for option, value in CONF.items(MODE, raw=True):
    OPTIONS[option] = value

#SUPPORTED_NOAA_SATELLITES = OPTIONS.get('supported_noaa_satellites')
SUPPORTED_NOAA_SATELLITES = ['NOAA-19', 'NOAA-18', 'NOAA-16', 'NOAA-15']
SUPPORTED_METOP_SATELLITES = ['Metop-B', 'Metop-A', 'Metop-C']

TLE_SATNAME = {'NOAA-19': 'NOAA 19', 'NOAA-18': 'NOAA 18',
               'NOAA-15': 'NOAA 15',
               'Metop-A': 'METOP-A', 'Metop-B': 'METOP-B',
               'Metop-C': 'METOP-C'}

METOP_NAME = {'metop01': 'Metop-B', 'metop02': 'Metop-A'}
METOP_NAME_INV = {'metopb': 'metop01', 'metopa': 'metop02'}
SATELLITE_NAME = {'NOAA-19': 'noaa19', 'NOAA-18': 'noaa18',
                  'NOAA-15': 'noaa15',
                  'Metop-A': 'metop02', 'Metop-B': 'metop01',
                  'Metop-C': 'metop03'}

# metop_sats = OPTIONS.get('supported_metop_satellites')
# SUPPORTED_METOP_SATELLITES = []
# for sat in metop_sats:
#     SUPPORTED_METOP_SATELLITES.append(METOP_NAME.get(sat, sat))

SENSOR_NAMES = ['amsu-a', 'amsu-b', 'mhs', 'avhrr/3', 'hirs/4']
SENSOR_NAME_CONVERTER = {
    'amsua': 'amsu-a', 'amsub': 'amsu-b', 'hirs': 'hirs/4',
    'mhs': 'mhs', 'avhrr': 'avhrt/3'}

METOP_NUMBER = {'b': '01', 'a': '02'}

SERVERNAME = OPTIONS['servername']

_AAPP_STAT_FILE = OPTIONS.get('aapp_stat_file', os.path.join(WORKING_DIR,
                                                             'aapp_statistics.log'))

AAPP_OUT_DIR = OPTIONS['aapp_out_dir']
METOP_IN_DIR = OPTIONS['metop_lvl0_dir']


import logging
LOG = logging.getLogger(__name__)

#: Default time format
_DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

#: Default log format
_DEFAULT_LOG_FORMAT = '[%(levelname)s: %(asctime)s : %(name)s] %(message)s'

_AAPP_LOG_FILE = OPTIONS.get('aapp_log_file', None)

from urlparse import urlparse
import posttroll.subscriber
from posttroll.publisher import Publish
from posttroll.message import Message
from trollduction.helper_functions import overlapping_timeinterval

import tempfile
from glob import glob
import os
import shutil
import aapp_stat
import threading
from subprocess import Popen, PIPE, STDOUT
from datetime import timedelta, datetime


def nonblock_read(output):
    """An attempt to catch any hangup in reading the output (stderr/stdout)
    from subprocess"""
    import fcntl
    fd = output.fileno()

    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.readline()
    except:
        return ''


def reset_job_registry(objdict, key, start_end_times):
    """Remove job key from registry"""

    LOG.debug("Register: " + str(objdict))
    starttime, endtime = start_end_times
    if key in objdict:
        if objdict[key] and len(objdict[key]) > 0:
            objdict[key].remove(start_end_times)
            LOG.debug("Release/reset job-key " + str(key) + " " +
                      str(starttime) + " " + str(endtime) + " from job registry")
            LOG.debug("Register: " + str(objdict))
            return

    LOG.warning("Nothing to reset/release - " +
                "Register didn't contain any entry matching: " +
                str(key))
    return


class AappLvl1Processor(object):

    """
    Container for the Metop/NOAA level-1 processing based on AAPP

    """

    def __init__(self):

        self.lvl1_home = OPTIONS['aapp_out_dir']
        self.fullswath = True  # Always a full swath (never HRPT granules)
        self.ishmf = False
        self.working_dir = None
        self.level0_filename = None
        self.starttime = None
        self.endtime = None
        self.platform_name = "Unknown"
        self.satnum = "0"
        self.orbit = "00000"
        self.result_files = None
        self.level0files = None

        self.job_register = {}

        self.initialise()

    def initialise(self):
        """Initialise the processor"""
        self.working_dir = None
        self.level0_filename = None
        self.starttime = None
        self.endtime = None
        self.platform_name = "Unknown"
        self.satnum = "0"
        self.orbit = "00000"
        self.result_files = []
        self.level0files = {}

    def cleanup_aapp_workdir(self):
        """Clean up the AAPP working dir after processing"""

        filelist = glob('%s/*' % self.working_dir)
        dummy = [os.remove(s) for s in filelist if os.path.isfile(s)]
        filelist = glob('%s/*' % self.working_dir)
        LOG.info("Number of items left after cleaning working dir = " +
                 str(len(filelist)))
        LOG.debug("Files: " + str(filelist))
        shutil.rmtree(self.working_dir)
        return

    def pack_aapplvl1_files(self, subd):
        return pack_aapplvl1_files(self.result_files, self.lvl1_home, subd,
                                   self.satnum)

    def move_lvl1dir(self):
        if len(self.result_files) == 0:
            LOG.warning("No files in directory to move!")
            return {}

        # Get the subdirname:
        path = os.path.dirname(self.result_files[0])
        subd = os.path.basename(path)
        LOG.debug("path = " + str(path))
        LOG.debug("lvl1_home = " + self.lvl1_home)
        try:
            shutil.move(path, self.lvl1_home)
        except shutil.Error:
            LOG.warning("Directory already exists: " + str(subd))

        if self.orbit == '00000' or self.orbit == None:
            # Extract the orbit number from the sub-dir name:
            dummy, dummy, dummy, self.orbit = subd.split('_')

        # Return a dict with sensor and level for each filename:
        filenames = glob(os.path.join(self.lvl1_home, subd, '*'))
        LOG.info(filenames)

        retv = {}
        for fname in filenames:
            mstr = os.path.basename(fname).split('_')[0]
            if mstr == 'hrpt':
                lvl = '1b'
                instr = 'avhrr/3'
            else:
                lvl = mstr[-2:]
                try:
                    instr = SENSOR_NAME_CONVERTER[mstr[0:-3]]
                except KeyError:
                    LOG.warning("Sensor name will not be converted %s" %
                                str(mstr[0:-3]))
                    LOG.debug("mstr = " + str(mstr))
                    instr = mstr[0:-3]

            retv[fname] = {'level': lvl, 'sensor': instr}

        LOG.info(str(retv))

        return retv

    def run(self, msg):
        """Start the AAPP level 1 processing on either a NOAA HRPT file or a
        set of Metop HRPT files"""

        # Avoid 'collections' and other stuff:
        if msg is None or msg.type != 'file':
            return True

        LOG.debug("Received message: " + str(msg))
        LOG.debug(
            "Supported Metop satellites: " + str(SUPPORTED_METOP_SATELLITES))
        try:
            if (msg.data['platform_name'] not in SUPPORTED_NOAA_SATELLITES and
                    msg.data['platform_name'] not in SUPPORTED_METOP_SATELLITES):
                LOG.info("Not a NOAA/Metop scene. Continue...")
                return True
        except Exception, err:
            LOG.warning(str(err))
            return True

        self.platform_name = msg.data['platform_name']
        LOG.debug("Satellite = " + str(self.platform_name))

        LOG.debug("")
        LOG.debug("\tMessage:")
        LOG.debug(str(msg))
        urlobj = urlparse(msg.data['uri'])
        server = urlobj.netloc
        LOG.debug('Server = <' + str(server) + '>')
        if len(server) > 0 and server != SERVERNAME:
            LOG.warning("Server %s not the current one: %s" % (str(server),
                                                               SERVERNAME))
            return True

        LOG.info("Ok... " + str(urlobj.netloc))
        LOG.info("Sat and Sensor: " + str(msg.data['platform_name'])
                 + " " + str(msg.data['sensor']))

        self.starttime = msg.data['start_time']
        try:
            self.endtime = msg.data['end_time']
        except KeyError:
            LOG.warning(
                "No end_time in message! Guessing start_time + 14 minutes...")
            self.endtime = msg.data['start_time'] + timedelta(seconds=60 * 14)

        start_orbnum = None
        try:
            import pyorbital.orbital as orb
            sat = orb.Orbital(
                TLE_SATNAME.get(self.platform_name, self.platform_name))
            start_orbnum = sat.get_orbit_number(self.starttime)
        except ImportError:
            LOG.warning("Failed importing pyorbital, " +
                        "cannot calculate orbit number")
        except AttributeError:
            LOG.warning("Failed calculating orbit number using pyorbital")
            LOG.warning("platform name = " +
                        str(TLE_SATNAME.get(self.platform_name, self.platform_name)) + " " +
                        str(self.platform_name))

        LOG.info(
            "Orbit number determined from pyorbital = " + str(start_orbnum))
        try:
            self.orbit = int(msg.data['orbit_number'])
        except KeyError:
            LOG.warning("No orbit_number in message! Set to none...")
            self.orbit = None

        if start_orbnum and self.orbit != start_orbnum:
            LOG.warning("Correcting orbit number: Orbit now = " +
                        str(start_orbnum) + " Before = " + str(self.orbit))
            self.orbit = start_orbnum
        else:
            LOG.debug(
                'Orbit number in message determined to be okay and not changed...')

        if self.platform_name in SUPPORTED_METOP_SATELLITES:
            metop_id = SATELLITE_NAME[self.platform_name].split('metop')[1]
            self.satnum = METOP_NUMBER.get(metop_id, metop_id)
        else:
            self.satnum = SATELLITE_NAME[self.platform_name].strip('noaa')

        year = self.starttime.year
        keyname = str(self.platform_name)
        LOG.debug("Keyname = " + str(keyname))
        LOG.debug("Start: job register = " + str(self.job_register))

        # Use sat id, start and end time as the unique identifier of the scene!
        if keyname in self.job_register and len(self.job_register[keyname]) > 0:
            # Go through list of start,end time tuples and see if the current
            # scene overlaps with any:
            status = overlapping_timeinterval((self.starttime, self.endtime),
                                              self.job_register[keyname])
            if status:
                LOG.warning("Processing of scene " + keyname +
                            " " + str(status[0]) + " " + str(status[1]) +
                            " with overlapping time have been launched previously")
                LOG.info("Skip it...")
                return True
            else:
                LOG.debug(
                    "No overlap with any recently processed scenes...")

        scene_id = (str(self.platform_name) + '_' +
                    self.starttime.strftime('%Y%m%d%H%M%S') +
                    '_' + self.endtime.strftime('%Y%m%d%H%M%S'))
        LOG.debug("scene_id = " + str(scene_id))

        # Check for keys representing the same scene (slightly different
        # start/end times):
        LOG.debug("Level-0files = " + str(self.level0files))
        for key in self.level0files:
            pltrfn, startt, endt = key.split('_')
            if not self.platform_name == pltrfn:
                continue
            t1_ = datetime.strptime(startt, '%Y%m%d%H%M%S')
            t2_ = datetime.strptime(endt, '%Y%m%d%H%M%S')
            if (abs(self.starttime - t1_).seconds < 60 and
                    abs(self.endtime - t2_).seconds < 60):
                # It is the same scene!
                LOG.debug(
                    "It is the same scene, though the file times differ a bit...")
                scene_id = key
                break

        LOG.debug("scene_id = " + str(scene_id))
        if scene_id in self.level0files:
            LOG.debug("Level-0files = " + str(self.level0files[scene_id]))
        else:
            LOG.debug("No level-0files yet...")

        self.level0_filename = urlobj.path
        dummy, fname = os.path.split(self.level0_filename)

        if fname.find('.hmf') > 0:
            self.ishmf = True
        else:
            LOG.info("File is not a hmf file, " +
                     "probably a Metop file or a NOAA from DMI: " + str(fname))

        LOG.debug("Sensor = " + str(msg.data['sensor']))
        LOG.debug("type: " + str(type(msg.data['sensor'])))
        if type(msg.data['sensor']) in [str, unicode]:
            sensors = [msg.data['sensor']]
        elif type(msg.data['sensor']) is list:
            sensors = msg.data['sensor']
        else:
            sensors = []
            LOG.warning('Failed interpreting sensor(s)!')

        LOG.info("Sensor(s): " + str(sensors))
        sensor_ok = False
        for sensor in sensors:
            if sensor in SENSOR_NAMES:
                sensor_ok = True
                break
        if not sensor_ok:
            LOG.info("No required sensors....")
            return True

        if scene_id not in self.level0files:
            LOG.debug("Reset level0files: scene_id = " + str(scene_id))
            self.level0files[scene_id] = []

        for sensor in sensors:
            item = (self.level0_filename, sensor)
            if item not in self.level0files[scene_id]:
                self.level0files[scene_id].append(item)
                LOG.debug("Appending item to list: " + str(item))
            else:
                LOG.debug("item already in list: " + str(item))

        if len(self.level0files[scene_id]) < 4:
            LOG.info("Not enough sensor data available yet. " +
                     "Level-0files = " +
                     str(self.level0files[scene_id]))
            return True
        else:
            LOG.info(
                "Level 0 files ready: " + str(self.level0files[scene_id]))

        if not self.working_dir:
            try:
                self.working_dir = tempfile.mkdtemp(dir=AAPP_WORKDIR)
            except OSError:
                self.working_dir = tempfile.mkdtemp()
            finally:
                LOG.info("Create new working dir...")

        LOG.info("Working dir = " + str(self.working_dir))

        my_env = os.environ.copy()
        my_env['DYN_WRK_DIR'] = self.working_dir
        LOG.info(
            "working dir: self.working_dir = " + str(self.working_dir))
        for envkey in my_env:
            LOG.debug("ENV: " + str(envkey) + " " + str(my_env[envkey]))

        if self.platform_name in SUPPORTED_NOAA_SATELLITES:
            LOG.info("This is a NOAA scene. Start the NOAA processing!")
            LOG.info("Process the file %s" % self.level0_filename)

            cmdseq = (NOAA_RUN_SCRIPT + ' -Y ' + str(year) + ' ' +
                      self.level0_filename)
            LOG.info("Command sequence: " + str(cmdseq))
            # Run the command:
            aapplvl1_proc = Popen(cmdseq,
                                  cwd=self.working_dir,
                                  shell=True, env=my_env,
                                  stderr=PIPE, stdout=PIPE)

        elif self.platform_name in SUPPORTED_METOP_SATELLITES:
            LOG.info("This is a Metop scene. Start the METOP processing!")
            LOG.info("Process the scene %s %s" %
                     (self.platform_name, str(self.orbit)))

            sensor_filename = {}
            for (fname, instr) in self.level0files[scene_id]:
                sensor_filename[instr] = os.path.basename(fname)

            for instr in sensor_filename.keys():
                if instr not in SENSOR_NAMES:
                    LOG.error("Sensor name mismatch! name = " + str(instr))
                    return True

            cmdstr = "%s -d %s -a %s -u %s -m %s -h %s -o %s" % (METOP_RUN_SCRIPT,
                                                                 METOP_IN_DIR,
                                                                 sensor_filename[
                                                                     'avhrr/3'],
                                                                 sensor_filename[
                                                                     'amsu-a'],
                                                                 sensor_filename[
                                                                     'mhs'],
                                                                 sensor_filename[
                                                                     'hirs/4'],
                                                                 AAPP_OUT_DIR)
            LOG.info("Command sequence: " + str(cmdstr))
            # Run the command:
            aapplvl1_proc = Popen(cmdstr,
                                  cwd=self.working_dir,
                                  shell=True, env=my_env,
                                  stderr=PIPE, stdout=PIPE)

        # Taking the stderr before stdout seems to be better preventing a
        # hangup!  AD, 2013-03-07
        while True:
            line = nonblock_read(aapplvl1_proc.stderr)
            if not line:
                break
            LOG.info(line)

        while True:
            line = nonblock_read(aapplvl1_proc.stdout)
            if not line:
                break
            LOG.info(line)

        aapplvl1_proc.poll()
        dummy = aapplvl1_proc.returncode
        LOG.info("Before call to communicate:")
        out, err = aapplvl1_proc.communicate()

        lines = out.splitlines()
        for line in lines:
            LOG.info(line)

        lines = err.splitlines()
        for line in lines:
            LOG.info(line)

        LOG.info("Communicate done...")

        LOG.info(
            "Ready with AAPP level-1 processing on NOAA scene: " + str(fname))
        LOG.info(
            "working dir: self.working_dir = " + str(self.working_dir))

        # Add to job register to avoid this to be run again
        if keyname not in self.job_register.keys():
            self.job_register[keyname] = []

        self.job_register[keyname].append((self.starttime, self.endtime))
        LOG.debug("End: job register = " + str(self.job_register))

        # Block any future run on this scene for x (e.g. 10) minutes from now
        t__ = threading.Timer(
            10 * 60.0, reset_job_registry, args=(self.job_register,
                                                 str(self.platform_name),
                                                 (self.starttime, self.endtime)))
        t__.start()

        LOG.debug("After timer call: job register = " + str(self.job_register))

        self.result_files = get_aapp_lvl1_files(
            self.working_dir, msg.data['platform_name'])

        LOG.info("Output files: " + str(self.result_files))

        statresult = aapp_stat.do_noaa_and_metop(self.level0_filename,
                                                 SATELLITE_NAME.get(self.platform_name,
                                                                    self.platform_name),
                                                 self.starttime)
        if os.path.exists(_AAPP_STAT_FILE):
            fd = open(_AAPP_STAT_FILE, "r")
            lines = fd.readlines()
            fd.close()
        else:
            lines = []

        lines = lines + [statresult + '\n']
        fd = open(_AAPP_STAT_FILE, "w")
        fd.writelines(lines)
        fd.close()

        return False


def aapp_rolling_runner():
    """The AAPP runner. Listens and triggers processing on Metop/NOAA HRPT
    level 0 files dispatched from Nimbus."""

    LOG.info("*** Start the NOAA/Metop HRPT AAPP runner:")

    aapp_proc = AappLvl1Processor()

    with posttroll.subscriber.Subscribe('', ['HRPT/0', 'EPS/0'], True) as subscr:
        with Publish('aapp_runner', 0) as publisher:
            while True:
                aapp_proc.initialise()
                for msg in subscr.recv(timeout=90):
                    status = aapp_proc.run(msg)
                    if not status:
                        break  # end the loop and reinitialize!

                tobj = aapp_proc.starttime
                LOG.info("Time used in sub-dir name: " +
                         str(tobj.strftime("%Y-%m-%d %H:%M")))
                if aapp_proc.platform_name.startswith('Metop'):
                    subd = create_subdirname(tobj, aapp_proc.platform_name,
                                             aapp_proc.orbit)
                    LOG.info("Create sub-directory for level-1 files: %s" %
                             str(subd))
                    level1_files = aapp_proc.pack_aapplvl1_files(subd)
                else:
                    LOG.info("Move sub-directory with NOAA level-1 files")
                    LOG.debug(
                        "Orbit BEFORE call to move_lvl1dir: " + str(aapp_proc.orbit))
                    level1_files = aapp_proc.move_lvl1dir()
                    LOG.debug(
                        "Orbit AFTER call to move_lvl1dir: " + str(aapp_proc.orbit))

                publish_level1(publisher, level1_files,
                               aapp_proc.platform_name,
                               aapp_proc.orbit,
                               aapp_proc.starttime,
                               aapp_proc.endtime)

                if aapp_proc.working_dir:
                    LOG.info("Cleaning up directory %s" %
                             aapp_proc.working_dir)
                    aapp_proc.cleanup_aapp_workdir()

    return


def publish_level1(publisher, result_files, satellite, orbit, start_t, end_t):
    """Publish the messages that AAPP lvl1 files are ready
    """
    # Now publish:
    for key in result_files:
        resultfile = key
        LOG.debug("File: " + str(os.path.basename(resultfile)))
        filename = os.path.split(resultfile)[1]
        to_send = {}
        to_send['uri'] = ('ssh://%s/%s' % (SERVERNAME, resultfile))
        to_send['uid'] = filename
        to_send['sensor'] = result_files[key]['sensor']
        to_send['platform_name'] = satellite
        to_send['orbit_number'] = int(orbit)
        to_send['format'] = 'AAPP-HRPT'
        to_send['type'] = 'Binary'
        to_send['data_processing_level'] = result_files[key]['level']
        LOG.debug('level in message: ' + str(to_send['data_processing_level']))
        environment = MODE
        to_send['start_time'], to_send['end_time'] = start_t, end_t
        msg = Message('/' + str(to_send['format']) + '/' +
                      str(to_send['data_processing_level']) +
                      '/norrköping/' + environment + '/polar/direct_readout/',
                      "file", to_send).encode()
        LOG.debug("sending: " + str(msg))
        publisher.send(msg)


def get_aapp_lvl1_files(level1_dir, satid):
    """Get the aapp level-1 filenames for the NOAA/Metop direct readout
    swath"""

    if satid in SUPPORTED_METOP_SATELLITES:
        # Level 1b/c data:
        lvl1_files = (glob(os.path.join(level1_dir, '*.l1b')) +
                      glob(os.path.join(level1_dir, '*.l1c')) +
                      glob(os.path.join(level1_dir, '*.l1d')))
    else:
        # SUBDIR example: noaa18_20140826_1108_47748
        LOG.debug(
            'level1_dir = ' + str(level1_dir) + ' satid  = ' + str(satid))
        matchstr = os.path.join(
            level1_dir, SATELLITE_NAME.get(satid, satid) + '_????????_????_?????/') + '*'
        LOG.debug(matchstr)
        lvl1_files = glob(matchstr)

    return lvl1_files


def create_subdirname(obstime, satid, orbnum):
    """Generate the pps subdirectory name from the start observation time, ex.:
    'noaa19_20120405_0037_02270'"""
    return (SATELLITE_NAME.get(satid, satid) +
            obstime.strftime('_%Y%m%d_%H%M_') +
            '%.5d' % orbnum)


def pack_aapplvl1_files(aappfiles, base_dir, subdir, satnum):
    """Copy the AAPP lvl1 files to the sub-directory under the pps directory
    structure"""
    # aman => amsua
    # ambn => amsub (satnum <= 17)
    # ambn => mhs (satnum > 17)
    # hrsn => hirs
    # msun => msu

    # Store the sensor name and the level corresponding to the file:
    sensor_and_level = {}

    name_converter = {'avhr': 'avhrr',
                      'aman': 'amsua',
                      'hrsn': 'hirs',
                      'msun': 'msu',
                      'hrpt': 'hrpt'
                      }
    not_considered = ['dcsn', 'msun']
    path = os.path.join(base_dir, subdir)
    if not os.path.exists(path):
        os.mkdir(path)

    LOG.info("Number of AAPP lvl1 files: " + str(len(aappfiles)))
    # retvl = []
    for aapp_file in aappfiles:
        fname = os.path.basename(aapp_file)
        in_name, ext = fname.split('.')
        if in_name in not_considered:
            continue

        if in_name == 'ambn':
            instr = 'mhs'
            try:
                if int(satnum) <= 17:
                    instr = 'amsub'
            except ValueError:
                pass
            firstname = instr + ext
            level = ext.strip('l')
        elif in_name == 'hrpt':
            firstname = name_converter.get(in_name)
            instr = 'avhrr/3'
            # Could also be 'avhrr'. Will anyhow be converted below...
            level = '1b'
        else:
            instr = name_converter.get(in_name, in_name)
            LOG.debug("Sensor = " + str(instr) + " from " + str(in_name))
            firstname = instr + ext
            level = ext.strip('l')

        newfilename = os.path.join(path, "%s_%s.%s" % (firstname,
                                                       subdir, ext))
        LOG.info("Copy aapp-file to destination: " + newfilename)
        shutil.copy(aapp_file, newfilename)
        # retvl.append(newfilename)
        sensor_and_level[newfilename] = {
            'sensor': SENSOR_NAME_CONVERTER.get(instr, instr),
            'level': level}

    return sensor_and_level
    # return retvl

# ----------------------------------
if __name__ == "__main__":

    from logging import handlers

    if _AAPP_LOG_FILE:
        ndays = int(OPTIONS["log_rotation_days"])
        ncount = int(OPTIONS["log_rotation_backup"])
        handler = handlers.TimedRotatingFileHandler(_AAPP_LOG_FILE,
                                                    when='midnight',
                                                    interval=ndays,
                                                    backupCount=ncount,
                                                    encoding=None,
                                                    delay=False,
                                                    utc=True)

        handler.doRollover()
    else:
        handler = logging.StreamHandler(sys.stderr)

    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt=_DEFAULT_LOG_FORMAT,
                                  datefmt=_DEFAULT_TIME_FORMAT)
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(logging.DEBUG)
    logging.getLogger('posttroll').setLevel(logging.INFO)

    LOG = logging.getLogger('aapp_runner')

    aapp_rolling_runner()
