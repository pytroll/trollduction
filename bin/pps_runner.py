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

"""Posttroll runner for PPS
"""
import os
import ConfigParser

CONFIG_PATH = os.environ.get('PPSRUNNER_CONFIG_DIR', './')
PPS_SCRIPT = os.environ['PPS_SCRIPT']

CONF = ConfigParser.ConfigParser()
CONF.read(os.path.join(CONFIG_PATH, "pps_config.cfg"))

MODE = os.getenv("SMHI_MODE")
if MODE is None:
    MODE = "offline"


OPTIONS = {}
for option, value in CONF.items(MODE, raw=True):
    OPTIONS[option] = value

#PPS_OUTPUT_DIR = os.environ.get('SM_PRODUCT_DIR', OPTIONS['pps_outdir'])
PPS_OUTPUT_DIR = OPTIONS['pps_outdir']

LEVEL1_PUBLISH_PORT = 9031
SERVERNAME = OPTIONS['servername']

SUPPORTED_NOAA_SATELLITES = ['NOAA-15', 'NOAA-18', 'NOAA-19']
SUPPORTED_METOP_SATELLITES = ['Metop-B', 'Metop-A']
SUPPORTED_EOS_SATELLITES = ['EOS-Terra', 'EOS-Aqua']
SUPPORTED_JPSS_SATELLITES = ['Suomi-NPP', 'JPSS-1', 'JPSS-2']

SUPPORTED_PPS_SATELLITES = (SUPPORTED_NOAA_SATELLITES +
                            SUPPORTED_METOP_SATELLITES +
                            SUPPORTED_EOS_SATELLITES +
                            SUPPORTED_JPSS_SATELLITES)

JPSS_NAME = {'Suomi-NPP': 'npp'}
EOS_NAME = {'EOS-Aqua': 'eos2', "EOS-Terra": 'eos1'}
GEOLOC_PREFIX = {'EOS-Aqua': 'MYD03', 'EOS-Terra': 'MOD03'}
DATA1KM_PREFIX = {'EOS-Aqua': 'MYD021km', 'EOS-Terra': 'MOD021km'}

PPS_INSTRUMENTS = ['amsua', 'amsub', 'mhs', 'avhrr', 'viirs', 'modis']

METOP_NAME_LETTER = {'metop01': 'metopb', 'metop02': 'metopa'}
METOP_NAME = {'metop01': 'Metop-B', 'metop02': 'Metop-A'}
METOP_NAME_INV = {'metopb': 'metop01', 'metopa': 'metop02'}

SATELLITE_NAME = {'NOAA-19': 'noaa19', 'NOAA-18': 'noaa18',
                  'NOAA-15': 'noaa15',
                  'Metop-A': 'metop02', 'Metop-B': 'metop01',
                  'Metop-C': 'metop03',
                  'Suomi-NPP': 'npp',
                  'EOS-Aqua': 'eos2', 'EOS-Terra': 'eos1'}

METOP_INSTRUMENT = {'amsu-a': 'amsua', 'avhrr/3': 'avhrr',
                    'amsu-b': 'amsub', 'hirs/4': 'hirs'}
METOP_NUMBER = {'b': '01', 'a': '02'}


import logging
LOG = logging.getLogger(__name__)

#: Default time format
_DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

#: Default log format
_DEFAULT_LOG_FORMAT = '[%(levelname)s: %(asctime)s : %(name)s] %(message)s'

_PPS_LOG_FILE = OPTIONS.get('pps_log_file', os.environ['PPSRUNNER_LOG_FILE'])

import sys
from glob import glob
import shutil

from urlparse import urlparse
import posttroll.subscriber
from posttroll.publisher import Publish
from posttroll.message import Message

from subprocess import Popen, PIPE, STDOUT
import threading
from datetime import datetime, timedelta


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


def get_outputfiles(path, satid, orb):
    """From the directory path and satellite id and orbit number scan the
    directory and find all pps output files matching that scene and return the
    full filenames"""

    from glob import glob
    matchstr = (os.path.join(path, 'S_NWC') + '*' +
                str(METOP_NAME_LETTER.get(satid, satid)) +
                '_' + str(orb) + '*.nc')
    LOG.debug(
        "Match string to do a file globbing on output files: " + str(matchstr))
    return glob(matchstr)


def reset_job_registry(objdict, key):
    """Remove job key from registry"""
    LOG.debug("Release/reset job-key " + str(key) + " from job registry")
    if key in objdict:
        objdict.pop(key)
    else:
        LOG.warning("Nothing to reset/release - " +
                    "Register didn't contain any entry matching: " +
                    str(key))

    return


def terminate_process(popen_obj, scene):
    """Terminate a Popen process"""
    if popen_obj.returncode == None:
        popen_obj.terminate()
        LOG.info(
            "Process timed out and pre-maturely terminated. Scene: " + str(scene))
    else:
        LOG.info(
            "Process finished before time out - workerScene: " + str(scene))
    return


def pps_worker(publisher, scene, semaphore_obj, queue):
    """Spawn/Start a PPS run on a new thread if available

        scene = {'satid': satid, 'orbit': orbit,
                 'satday': satday, 'sathour': sathour,
                 'starttime': starttime, 'endtime': endtime}
    """

    semaphore_obj.acquire()
    cmdstr = "%s %s %s %s %s" % (PPS_SCRIPT, scene['satid'],
                                 scene['orbit'], scene['satday'],
                                 scene['sathour'])
    LOG.info("Command " + cmdstr)
    my_env = os.environ.copy()
    for envkey in my_env:
        LOG.debug("ENV: " + str(envkey) + " " + str(my_env[envkey]))

    LOG.debug("PPS_OUTPUT_DIR = " + str(PPS_OUTPUT_DIR))
    LOG.debug("...from config file = " + str(OPTIONS['pps_outdir']))
    pps_proc = Popen(cmdstr, shell=True, stderr=PIPE, stdout=PIPE)
    t__ = threading.Timer(
        25 * 60.0, terminate_process, args=(pps_proc, scene, ))
    t__.start()

    while True:
        line = pps_proc.stdout.readline()
        if not line:
            break
        LOG.info(line)

    while True:
        errline = pps_proc.stderr.readline()
        if not errline:
            break
        LOG.info(errline)

    pps_proc.wait()

    LOG.info(
        "Ready with PPS level-2 processing on scene: " + str(scene))

    # Now check what netCDF out was produced and publish them:
    result_files = get_outputfiles(
        PPS_OUTPUT_DIR, scene['satid'], scene['orbit'])
    LOG.info("Output files: " + str(result_files))
    queue.put((publisher, scene, result_files))
    semaphore_obj.release()
    return


class FilePublisher(threading.Thread):

    """A publisher for the PPS result files. Picks up the return value from the
    pps_worker when ready, and publishes the files via posttroll"""

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.loop = True
        self.queue = queue
        self.jobs = {}

    def stop(self):
        """Stops the file publisher"""
        self.loop = False
        self.queue.put(None)

    def run(self):

        while self.loop:
            retv = self.queue.get()
            if retv != None:
                LOG.info("Publish the files...")
                publisher, scene, result_files = retv

                keyname = str(scene['satid']) + '_' + str(scene['orbit'])
                if keyname not in self.jobs:
                    LOG.warning("Scene-run seems unregistered! Forget it...")
                else:
                    if isinstance(self.jobs[keyname], datetime):
                        dt_ = datetime.utcnow() - self.jobs[keyname]
                        LOG.info("PPS on scene " + str(keyname) +
                                 " finished. It took: " + str(dt_))

                    self.jobs[keyname] = False
                # Block any future run on this scene for x minutes from now
                t__ = threading.Timer(
                    5 * 60.0, reset_job_registry, args=(self.jobs, keyname))
                t__.start()

                publish_level2(publisher, result_files,
                               scene['satid'],
                               scene['orbit'],
                               # scene['instrument'],
                               None,
                               scene['starttime'],
                               scene['endtime'])

            else:
                LOG.debug("Queue is empty...")


def publish_level2(publisher, result_files, sat, orb, instr, start_t, end_t):
    """Publish the messages that PPS lvl2 files are ready
    """
    # Now publish:
    for result_file in result_files:
        filename = os.path.split(result_file)[1]
        to_send = {}
        to_send['uri'] = ('ssh://%s/%s' % (SERVERNAME, result_file))
        to_send['filename'] = filename
        #to_send['instrument'] = instr
        to_send['platform_name'] = sat
        to_send['orbit_number'] = orb
        to_send['format'] = 'PPS'
        to_send['type'] = 'netCDF4'
        to_send['data_processing_level'] = '2'
        to_send['start_time'], to_send['end_time'] = start_t, end_t

        environment = MODE
        to_send['start_time'], to_send['end_time'] = start_t, end_t
        msg = Message('/' + to_send['format'] + '/' + to_send['data_processing_level'] +
                      '/norrköping/' + environment + '/polar/direct_readout/',
                      "file", to_send).encode()
        LOG.debug("sending: " + str(msg))
        publisher.send(msg)


def ready2run(msg, files4pps, job_register):
    """Check wether pps is ready to run or not"""
    #"""Start the PPS processing on a NOAA/Metop/S-NPP/EOS scene"""
    # LOG.debug("Received message: " + str(msg))
    if msg:
        if (msg.data['platform_name'] not in SUPPORTED_PPS_SATELLITES):
            LOG.info(str(msg.data['platform_name']) + ": " +
                     "Not a NOAA/Metop/S-NPP/Terra/Aqua scene. Continue...")
            return False

    elif msg is None:
        return False

    LOG.debug("Ready to run...")
    LOG.info("Got message: " + str(msg))
    urlobj = urlparse(msg.data['uri'])
    server = urlobj.netloc
    LOG.debug("Server = " + str(server))
    if server != SERVERNAME:
        LOG.warning("Server %s not the current one: %s" % (str(server),
                                                           SERVERNAME))
        return False
    LOG.info("Sat and Instrument: " + str(msg.data['platform_name'])
             + " " + str(msg.data['sensor']))
    if msg.data['sensor'] not in PPS_INSTRUMENTS:
        LOG.info("Data from sensor " + str(msg.data['sensor']) +
                 " not needed by PPS " +
                 "Continue...")
        return False

    if msg.data['platform_name'] in SUPPORTED_EOS_SATELLITES:
        if msg.data['sensor'] not in ['modis', ]:
            LOG.info(
                'Instrument ' + str(msg.data['sensor']) +
                ' not required for MODIS PPS processing...')
            return False
    elif msg.data['platform_name'] in SUPPORTED_JPSS_SATELLITES:
        if msg.data['instrument'] not in ['viirs', ]:
            LOG.info(
                'Instrument ' + str(msg.data['instrument']) +
                ' not required for S-NPP/VIIRS PPS processing...')
            return False
    else:
        if msg.data['instrument'] not in ['avhrr', 'amsua', 'amsub', 'mhs']:
            LOG.info(
                'Instrument ' + str(msg.data['instrument']) + ' not required...')
            return False
        if (msg.data['instrument'] in ['amsua', 'amsub', 'mhs'] and
                msg.data['data_processing_level'] != '1c'):
            LOG.info('Level not the required type for PPS for this instrument: ' +
                     str(msg.data['instrument']) + ' ' +
                     str(msg.data['data_processing_level']))
            return False

    # The orbit number is mandatory!
    orbit_number = int(msg.data['orbit_number'])
    LOG.debug("Orbit number: " + str(orbit_number))
    level1_filename = urlobj.path
    dummy, fname = os.path.split(level1_filename)

    #instrument = (msg.data['instrument'])
    platform_name = msg.data['platform_name']

    try:
        satid = SATELLITE_NAME[platform_name]
    except KeyError:
        LOG.info("Satellite not supported: " + str(platform_name))
        return False

    keyname = str(satid) + '_' + str(orbit_number)
    if keyname in job_register and job_register[keyname]:
        LOG.debug("Processing of scene " + str(keyname) +
                  " have already been launched...")
        return False

    if keyname not in files4pps:
        files4pps[keyname] = []

    if platform_name in SUPPORTED_EOS_SATELLITES:
        fname = os.path.basename(level1_filename)
        if (fname.startswith(GEOLOC_PREFIX[platform_name]) or
                fname.startswith(DATA1KM_PREFIX[platform_name])):
            files4pps[keyname].append(level1_filename)
    else:
        files4pps[keyname].append(level1_filename)

    if (platform_name in SUPPORTED_METOP_SATELLITES or
            platform_name in SUPPORTED_NOAA_SATELLITES):
        if len(files4pps[keyname]) < 3:
            LOG.info(
                "Not enough NOAA/Metop instrument data available yet...")
            return False
    elif platform_name in SUPPORTED_EOS_SATELLITES:
        if len(files4pps[keyname]) < 2:
            LOG.info("Not enough MODIS level 1 files available yet...")
            return False

    LOG.info("Level 1 files ready: " + str(files4pps[keyname]))

    if msg.data['platform_name'] in SUPPORTED_PPS_SATELLITES:
        LOG.info(
            "This is a PPS supported scene. Start the PPS lvl2 processing!")
        LOG.info("Process the scene (sat, orbit) = " +
                 str(satid) + ' ' + str(orbit_number))

        job_register[keyname] = datetime.utcnow()
        return True


def check_threads(threads):
    """Scan all threads and join those that are finished (dead)"""

    # LOG.debug(str(threading.enumerate()))
    for i, thread in enumerate(threads):
        if thread.is_alive():
            LOG.info("Thread " + str(i) + " alive...")
        else:
            LOG.info(
                "Thread " + str(i) + " is no more alive...")
            thread.join()
            threads.remove(thread)

    return


def pps_rolling_runner():
    """The PPS runner. Triggers processing of PPS main script once AAPP or CSPP
    is ready with a level-1 file"""

    LOG.info("*** Start the PPS level-2 runner:")

    sema = threading.Semaphore(3)
    import Queue
    q__ = Queue.Queue()

    pub_thread = FilePublisher(q__)
    pub_thread.start()

    files4pps = {}
    threads = []
    with posttroll.subscriber.Subscribe(['aapp_runner', 'modis_dr_runner',
                                         'viirs_dr_runner'],
                                        ['AAPP-HRPT', 'EOS/1', 'SDR'], True) as subscr:
        with Publish('pps_runner', 0, ['PPS', ]) as publisher:
            while True:
                status = False
                check_threads(threads)
                for msg in subscr.recv(timeout=90):
                    status = ready2run(msg, files4pps, pub_thread.jobs)
                    if status:
                        # end the loop and spawn a pps process on the scene
                        message = msg
                        break

                    check_threads(threads)

                LOG.info("Start spawning a PPS processor for the scene")

                urlobj = urlparse(message.data['uri'])
                orbit_number = int(message.data['orbit_number'])
                LOG.debug("Orbit number: " + str(orbit_number))
                level1_filename = urlobj.path

                LOG.info("Ok... " + str(urlobj.netloc))
                starttime = message.data['start_time']
                try:
                    endtime = message.data['end_time']
                except KeyError:
                    LOG.warning(
                        "No end_time in message! Guessing start_time + 14 minutes...")
                    endtime = message.data['start_time'] + \
                        timedelta(seconds=60 * 14)

                platform_name = message.data['platform_name']

                try:
                    satid = SATELLITE_NAME[platform_name]
                except KeyError:
                    raise IOError(
                        "Satellite not supported: " + str(platform_name))

                satday = starttime.strftime('%Y%m%d')
                sathour = starttime.strftime('%H%M')
                scene = {'satid': satid, 'orbit_number': orbit_number,
                         'satday': satday, 'sathour': sathour,
                         'starttime': starttime, 'endtime': endtime}

                t__ = threading.Thread(target=pps_worker, args=(publisher, scene,
                                                                sema, q__))
                threads.append(t__)
                t__.start()

                # Clean the files4pps dict:
                LOG.debug("files4pps: " + str(files4pps))
                keyname = str(satid) + '_' + str(orbit_number)
                try:
                    files4pps.pop(keyname)
                except KeyError:
                    LOG.warning("Failed trying to remove key " + str(keyname) +
                                " from dictionary files4pps")
                LOG.debug("After cleaning: files4pps = " + str(files4pps))

    LOG.info("Wait till all threads are dead...")
    while True:
        workers_ready = True
        for thread in threads:
            if thread.is_alive():
                workers_ready = False

        if workers_ready:
            break

    pub_thread.stop()

    return

if __name__ == "__main__":

    from logging import handlers

    if _PPS_LOG_FILE:
        ndays = int(OPTIONS["log_rotation_days"])
        ncount = int(OPTIONS["log_rotation_backup"])
        handler = handlers.TimedRotatingFileHandler(_PPS_LOG_FILE,
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

    LOG = logging.getLogger('pps_runner')

    pps_rolling_runner()
