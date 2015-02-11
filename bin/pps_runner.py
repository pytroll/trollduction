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
LVL1_NPP_PATH = os.environ.get('LVL1_NPP_PATH', None)
LVL1_EOS_PATH = os.environ.get('LVL1_EOS_PATH', None)


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

PPS_SENSORS = ['amsu-a', 'amsu-b', 'mhs', 'avhrr/3', 'viirs', 'modis']
NOAA_METOP_PPS_SENSORNAMES = ['avhrr/3', 'amsu-a', 'amsu-b', 'mhs']

METOP_NAME_LETTER = {'metop01': 'metopb', 'metop02': 'metopa'}
METOP_NAME = {'metop01': 'Metop-B', 'metop02': 'Metop-A'}
METOP_NAME_INV = {'metopb': 'metop01', 'metopa': 'metop02'}

SATELLITE_NAME = {'NOAA-19': 'noaa19', 'NOAA-18': 'noaa18',
                  'NOAA-15': 'noaa15',
                  'Metop-A': 'metop02', 'Metop-B': 'metop01',
                  'Metop-C': 'metop03',
                  'Suomi-NPP': 'npp',
                  'EOS-Aqua': 'eos2', 'EOS-Terra': 'eos1'}
SENSOR_LIST = {}
for sat in SATELLITE_NAME:
    if sat in ['NOAA-15']:
        SENSOR_LIST[sat] = ['avhrr/3', 'amsu-b', 'amsu-a']
    elif sat in ['EOS-Aqua', 'EOS-Terra']:
        SENSOR_LIST[sat] = 'modis'
    elif sat in ['Suomi-NPP', 'JPSS-1', 'JPSS-2']:
        SENSOR_LIST[sat] = 'viirs'
    else:
        SENSOR_LIST[sat] = ['avhrr/3', 'mhs', 'amsu-a']


METOP_SENSOR = {'amsu-a': 'amsua', 'avhrr/3': 'avhrr',
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
                '_' + str(orb) + '*.h5')
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
        popen_obj.kill()
        LOG.info(
            "Process timed out and pre-maturely terminated. Scene: " + str(scene))
    else:
        LOG.info(
            "Process finished before time out - workerScene: " + str(scene))
    return


def pps_worker(publisher, scene, semaphore_obj, queue):
    """Spawn/Start a PPS run on a new thread if available

        scene = {'satid': satid, 'orbit_number': orbit,
                 'satday': satday, 'sathour': sathour,
                 'starttime': starttime, 'endtime': endtime}
    """

    semaphore_obj.acquire()
    if scene['satid'] in SUPPORTED_EOS_SATELLITES:
        cmdstr = "%s %s %s %s %s" % (PPS_SCRIPT, SATELLITE_NAME[scene['satid']],
                                     scene['orbit_number'], scene['satday'],
                                     scene['sathour'])
    else:
        cmdstr = "%s %s %s 0 0" % (PPS_SCRIPT, SATELLITE_NAME[scene['satid']],
                                   scene['orbit_number'])

    if scene['satid'] in SUPPORTED_JPSS_SATELLITES and LVL1_NPP_PATH:
        cmdstr = cmdstr + ' ' + str(LVL1_NPP_PATH)
    elif scene['satid'] in SUPPORTED_EOS_SATELLITES and LVL1_EOS_PATH:
        cmdstr = cmdstr + ' ' + str(LVL1_EOS_PATH)

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
        PPS_OUTPUT_DIR, SATELLITE_NAME[scene['satid']], scene['orbit_number'])
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

                keyname = (str(scene['satid']) + '_' +
                           str(scene['orbit_number']) + '_' +
                           str(scene['starttime'].strftime('%Y%m%d%H%M')))
                if keyname not in self.jobs:
                    LOG.warning("Scene-run seems unregistered! Forget it...")
                else:
                    if isinstance(self.jobs[keyname], datetime):
                        dt_ = datetime.utcnow() - self.jobs[keyname]
                        LOG.info("PPS on scene " + str(keyname) +
                                 " finished. It took: " + str(dt_))
                    else:
                        LOG.warning(
                            "Not a datetime instance: jobs[%s]" % str(keyname) +
                            str(self.jobs[keyname]))

                    self.jobs[keyname] = False
                # Block any future run on this scene for x minutes from now
                t__ = threading.Timer(
                    5 * 60.0, reset_job_registry, args=(self.jobs, keyname))
                t__.start()

                publish_level2(publisher, result_files,
                               scene['satid'],
                               scene['orbit_number'],
                               scene['sensor'],
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
        to_send['uid'] = filename
        if instr:
            to_send['sensor'] = instr
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


def ready2run(msg, files4pps, job_register, sceneid):
    """Check wether pps is ready to run or not"""
    #"""Start the PPS processing on a NOAA/Metop/S-NPP/EOS scene"""
    # LOG.debug("Received message: " + str(msg))

    from trollduction.producer import check_uri

    if msg:
        if (msg.data['platform_name'] not in SUPPORTED_PPS_SATELLITES):
            LOG.info(str(msg.data['platform_name']) + ": " +
                     "Not a NOAA/Metop/S-NPP/Terra/Aqua scene. Continue...")
            return False

    elif msg is None:
        return False

    LOG.debug("Ready to run...")
    LOG.info("Got message: " + str(msg))

    uris = []
    if msg.type == 'dataset':
        LOG.info('Dataset: ' + str(msg.data['dataset']))
        LOG.info('\t...thus we can assume we have everything we need for PPS')
        for obj in msg.data['dataset']:
            uris.append(obj['uri'])
    elif msg.type == 'collection':
        if 'dataset' in msg.data['collection'][0]:
            for dataset in msg.data['collection']:
                uris.extend([mda['uri'] for mda in dataset['dataset']])
    elif msg.type == 'file':
        uris = [(msg.data['uri'])]
    else:
        LOG.debug(
            "Ignoring this type of message data: tyep = " + str(msg.type))
        return False

    # server = urlobj.netloc
    # server = urlparse(obj['uri']).netloc  # Assume server is the same for
    # all uri's!

    try:
        level1_files = check_uri(uris)
    except IOError:
        LOG.info('One or more files not present on this host!')
        return False

    LOG.info("Sat and Sensor: " + str(msg.data['platform_name'])
             + " " + str(msg.data['sensor']))
    if msg.data['sensor'] not in PPS_SENSORS:
        LOG.info("Data from sensor " + str(msg.data['sensor']) +
                 " not needed by PPS " +
                 "Continue...")
        return False

    if msg.data['platform_name'] in SUPPORTED_EOS_SATELLITES:
        if msg.data['sensor'] not in ['modis', ]:
            LOG.info(
                'Sensor ' + str(msg.data['sensor']) +
                ' not required for MODIS PPS processing...')
            return False
    elif msg.data['platform_name'] in SUPPORTED_JPSS_SATELLITES:
        if msg.data['sensor'] not in ['viirs', ]:
            LOG.info(
                'Sensor ' + str(msg.data['sensor']) +
                ' not required for S-NPP/VIIRS PPS processing...')
            return False
    else:
        if msg.data['sensor'] not in ['avhrr/3', 'amsu-a', 'amsu-b', 'mhs']:
            LOG.info(
                'Sensor ' + str(msg.data['sensor']) + ' not required...')
            return False
        if (msg.data['sensor'] in ['amsu-a', 'amsu-b', 'mhs'] and
                msg.data['data_processing_level'] != '1c'):
            LOG.info('Level not the required type for PPS for this sensor: ' +
                     str(msg.data['sensor']) + ' ' +
                     str(msg.data['data_processing_level']))
            return False

    # The orbit number is mandatory!
    orbit_number = int(msg.data['orbit_number'])
    LOG.debug("Orbit number: " + str(orbit_number))

    #sensor = (msg.data['sensor'])
    platform_name = msg.data['platform_name']

    if platform_name not in SATELLITE_NAME:
        LOG.warning("Satellite not supported: " + str(platform_name))
        return False

    if 'start_time' in msg.data:
        starttime = msg.data['start_time']
    else:
        starttime = None

    LOG.debug("Scene identifier = " + str(sceneid))
    LOG.debug("Job register = " + str(job_register))
    if sceneid in job_register and job_register[sceneid]:
        LOG.debug("Processing of scene " + str(sceneid) +
                  " have already been launched...")
        return False

    tdelta_thr = timedelta(seconds=180)  # 3 minutes
    key_entries = sceneid.split('_')
    if len(key_entries) == 3:
        for key in job_register.keys():
            firstpart = key.split('_')[0] + '_' + key.split('_')[1]
            this_firstpart = key_entries[0] + '_' + key_entries[1]
            LOG.debug('datetimes of entries: ' +
                      str(firstpart) + ' ' +
                      str(this_firstpart))
            if firstpart == this_firstpart:
                # Check if the times are approximately the same:
                tobj = datetime.strptime(key.split('_')[-1], '%Y%m%d%H%M')
                if starttime and abs(tobj - starttime) < tdelta_thr:
                    LOG.warning("This scene is very close to a previously " +
                                "processed scene! Don't do anything with it then...")
                    return False

    if sceneid not in files4pps:
        files4pps[sceneid] = []

    if platform_name in SUPPORTED_EOS_SATELLITES:
        for item in level1_files:
            fname = os.path.basename(item)
            if (fname.startswith(GEOLOC_PREFIX[platform_name]) or
                    fname.startswith(DATA1KM_PREFIX[platform_name])):
                files4pps[sceneid].append(item)
    else:
        for item in level1_files:
            fname = os.path.basename(item)
            files4pps[sceneid].append(fname)

    if (platform_name in SUPPORTED_METOP_SATELLITES or
            platform_name in SUPPORTED_NOAA_SATELLITES):
        if len(files4pps[sceneid]) < 3:
            LOG.info(
                "Not enough NOAA/Metop sensor data available yet...")
            return False
    elif platform_name in SUPPORTED_EOS_SATELLITES:
        if len(files4pps[sceneid]) < 2:
            LOG.info("Not enough MODIS level 1 files available yet...")
            return False

    if len(files4pps[sceneid]) > 10:
        LOG.info(
            "Number of level 1 files ready = " + str(len(files4pps[sceneid])))
        LOG.info("Scene = " + str(sceneid))
    else:
        LOG.info("Level 1 files ready: " + str(files4pps[sceneid]))

    if msg.data['platform_name'] in SUPPORTED_PPS_SATELLITES:
        LOG.info(
            "This is a PPS supported scene. Start the PPS lvl2 processing!")
        LOG.info("Process the scene (sat, orbit) = " +
                 str(platform_name) + ' ' + str(orbit_number))

        job_register[sceneid] = datetime.utcnow()
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
    with posttroll.subscriber.Subscribe("", ['AAPP-HRPT', 'EOS/1', 'SDR'],
                                        True) as subscr:
        with Publish('pps_runner', 0, ['PPS', ]) as publisher:
            while True:
                status = False
                check_threads(threads)
                for msg in subscr.recv(timeout=90):
                    keyname = None
                    if (msg and
                            'platform_name' in msg.data and
                            'orbit_number' in msg.data):
                        orbit_number = int(msg.data['orbit_number'])
                        platform_name = msg.data['platform_name']
                        starttime = None
                        if 'start_time' in msg.data:
                            starttime = msg.data['start_time']
                            keyname = (str(platform_name) + '_' +
                                       str(orbit_number) + '_' +
                                       str(starttime.strftime('%Y%m%d%H%M')))
                        else:
                            keyname = (str(platform_name) + '_' +
                                       str(orbit_number))

                    status = ready2run(msg, files4pps,
                                       pub_thread.jobs, keyname)
                    if status:
                        # end the loop and spawn a pps process on the scene
                        message = msg
                        break

                    check_threads(threads)

                LOG.info("Start spawning a PPS processor for the scene")
                orbit_number = int(message.data['orbit_number'])
                LOG.debug("Orbit number: = " + str(orbit_number))

                starttime = message.data['start_time']
                try:
                    endtime = message.data['end_time']
                except KeyError:
                    LOG.warning(
                        "No end_time in message! Guessing start_time + 14 minutes...")
                    endtime = message.data['start_time'] + \
                        timedelta(seconds=60 * 14)

                platform_name = message.data['platform_name']
                if platform_name not in SATELLITE_NAME:
                    raise IOError(
                        "Satellite not supported: " + str(platform_name))

                sensors = SENSOR_LIST.get(platform_name, None)
                satday = starttime.strftime('%Y%m%d')
                sathour = starttime.strftime('%H%M')
                scene = {'satid': platform_name, 'orbit_number': orbit_number,
                         'satday': satday, 'sathour': sathour,
                         'starttime': starttime, 'endtime': endtime,
                         'sensor': sensors}

                t__ = threading.Thread(target=pps_worker, args=(publisher, scene,
                                                                sema, q__))
                threads.append(t__)
                t__.start()

                # Clean the files4pps dict:
                LOG.debug("files4pps: " + str(files4pps))
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
