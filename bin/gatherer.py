#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015 Martin Raspaud

# Author(s): Martin Raspaud
#            Panu Lahtinen

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

"""Gather granule messages to send them in a bunch.
"""

from ConfigParser import RawConfigParser, NoOptionError
from trollsift import Parser, compose
from datetime import timedelta, datetime
from trollduction.collectors import trigger
from trollduction.collectors import region_collector
import time
import logging
import logging.handlers
import os.path
from posttroll import message, publisher
from mpop.projector import get_area_def

LOGGER = logging.getLogger(__name__)
CONFIG = RawConfigParser()
PUB = None


def get_metadata(fname):
    '''Parse metadata from the file.
    '''

    res = None
    for section in CONFIG.sections():
        if section == "default":
            continue
        try:
            parser = Parser(CONFIG.get(section, "pattern"))
        except NoOptionError:
            continue
        if not parser.validate(fname):
            continue
        res = parser.parse(fname)
        res.update(dict(CONFIG.items(section)))

        for key in ["watcher", "pattern", "timeliness"]:
            res.pop(key, None)

        if "duration" in res and "end_time" not in res:
            res["end_time"] = (res["start_time"] +
                               timedelta(seconds=int(res["duration"])))
        if "start_date" in res:
            res["start_time"] = datetime.combine(res["start_date"].date(),
                                                 res["start_time"].time())
            if "end_date" not in res:
                res["end_date"] = res["start_date"]
            del res["start_date"]
        if "end_date" in res:
            res["end_time"] = datetime.combine(res["end_date"].date(),
                                               res["end_time"].time())
            del res["end_date"]

        while res["start_time"] > res["end_time"]:
            res["end_time"] += timedelta(days=1)

        if "duration" in res:
            del res["duration"]

        res["uri"] = fname
        res["filename"] = os.path.basename(fname)

    return res


def terminator(metadata, publish_topic=None):
    """Dummy terminator function.
    """
    sorted_mda = sorted(metadata, key=lambda x: x["start_time"])

    mda = metadata[0].copy()

    if publish_topic is not None:
        LOGGER.info("Composing topic.")
        subject = compose(publish_topic, mda)
    else:
        LOGGER.warning("Using default topic.")
        subject = "/".join(("", mda["format"], mda["data_processing_level"],
                            ''))

    mda['end_time'] = sorted_mda[-1]['end_time']

    mda['collection'] = []

    for meta in sorted_mda:
        new_mda = {}
        for key in ['dataset', 'uri', 'uid']:
            if key in meta:
                new_mda[key] = meta[key]
            new_mda['start_time'] = meta['start_time']
            new_mda['end_time'] = meta['end_time']
        mda['collection'].append(new_mda)

    for key in ['dataset', 'uri', 'uid']:
        if key in mda:
            del mda[key]

    msg = message.Message(subject, "collection",
                          mda)
    LOGGER.info("sending %s", str(msg))
    PUB.send(str(msg))


def arg_parse():
    '''Handle input arguments.
    '''
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log",
                        help="File to log to (defaults to stdout)",
                        default=None)
    parser.add_argument("-v", "--verbose", help="print debug messages too",
                        action="store_true")
    parser.add_argument("config", help="config file to be used")

    return parser.parse_args()


def setup(regions, decoder):
    '''Setup the granule triggerer.
    '''

    granule_triggers = []

    for section in CONFIG.sections():
        if section == "default":
            continue

        timeliness = timedelta(minutes=CONFIG.getint(section, "timeliness"))
        try:
            duration = timedelta(seconds=CONFIG.getfloat(section, "duration"))
        except NoOptionError:
            duration = None
        collectors = [region_collector.RegionCollector(
            region, timeliness, duration) for region in regions]

        try:
            observer_class = CONFIG.get(section, "watcher")
            pattern = CONFIG.get(section, "pattern")
            parser = Parser(pattern)
            glob = parser.globify()
        except NoOptionError:
            observer_class = None

        try:
            publish_topic = CONFIG.get(section, "publish_topic")
        except NoOptionError:
            publish_topic = None

        if observer_class in ["PollingObserver", "Observer"]:
            LOGGER.debug("Using %s for %s", observer_class, section)
            granule_trigger = \
                trigger.WatchDogTrigger(collectors,
                                        terminator,
                                        decoder,
                                        [glob],
                                        observer_class,
                                        publish_topic=publish_topic)

        else:
            LOGGER.debug("Using posttroll for %s", section)
            granule_trigger = trigger.PostTrollTrigger(
                collectors, terminator,
                CONFIG.get(section, 'service').split(','),
                CONFIG.get(section, 'topics').split(','),
                publish_topic=publish_topic)
        granule_triggers.append(granule_trigger)

    return granule_triggers


def main():
    '''Main() for gatherer.
    '''

    global LOGGER
    global PUB

    opts = arg_parse()
    CONFIG.read(opts.config)

    if opts.log:
        handler = logging.handlers.TimedRotatingFileHandler(opts.log,
                                                            "midnight",
                                                            backupCount=7)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s: %(asctime)s :"
                                           " %(name)s] %(message)s",
                                           '%Y-%m-%d %H:%M:%S'))
    if opts.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    handler.setLevel(loglevel)
    logging.getLogger('').setLevel(loglevel)
    logging.getLogger('').addHandler(handler)
    logging.getLogger("posttroll").setLevel(logging.INFO)
    LOGGER = logging.getLogger("gatherer")

    decoder = get_metadata

    PUB = publisher.NoisyPublisher("gatherer")

    # TODO: get this from the product config files
    # NOTE: the product configs might not be locally available
    regions = [get_area_def(region)
               for region in CONFIG.get("default", "regions").split()]

    granule_triggers = setup(regions, decoder)

    PUB.start()

    for granule_trigger in granule_triggers:
        granule_trigger.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        LOGGER.info("Shutting down...")
        for granule_trigger in granule_triggers:
            granule_trigger.stop()
        PUB.stop()

if __name__ == '__main__':

    main()
