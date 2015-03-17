# -*- coding: utf-8 -*-
#
# Copyright (c) 2014, 2015
#
# Author(s):
#
#   Panu Lahtinen <panu.lahtinen@fmi.fi>
#   Martin Raspaud <martin.raspaud@smhi.se>
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''Trollduction module

TODO:
 - adjust docstrings to sphinx (see check_sunzen())
 - change messages to follow the posttroll way of doing
 - save data/images in a separate writer thread to avoid the I/O bottleneck
 - write a command receiver (for messages like reload_config/shutdown/restart)
 - implement a command sender also
 - load default config in case some parameters are missing in the config.ini
 - allow adding custom options per file for saving (eg format,
   tiles/stripes/tifftags)
 - add area-by-area selection for projection method
   (crude/nearest/<something new>)
'''

from .listener import ListenerContainer
from mpop.satellites import GenericFactory as GF
import time
from mpop.projector import get_area_def
from threading import Thread
from pyorbital import astronomy
import numpy as np
import os
import Queue
import logging
import logging.handlers
from fnmatch import fnmatch
from trollduction import helper_functions
from trollsift import compose
from urlparse import urlparse, urlunsplit
import socket
import shutil
from mpop.satout.cfscene import CFScene
from posttroll.publisher import Publish
from posttroll.message import Message
from pyresample.utils import AreaNotFound
from trollsched.satpass import Pass
from trollsched.boundary import Boundary, AreaDefBoundary
import errno
import netifaces

from xml.etree.ElementTree import tostring
LOGGER = logging.getLogger(__name__)

# Config watcher stuff

import pyinotify


def get_local_ips():
    inet_addrs = [netifaces.ifaddresses(iface).get(netifaces.AF_INET)
                  for iface in netifaces.interfaces()]
    ips = []
    for addr in inet_addrs:
        if addr is not None:
            for add in addr:
                ips.append(add['addr'])
    return ips


def check_uri(uri):
    """Check that the provided *uri* is on the local host and return the
    file path.
    """
    if isinstance(uri, (list, set, tuple)):
        paths = [check_uri(ressource) for ressource in uri]
        return paths
    url = urlparse(uri)
    try:
        url_ip = socket.gethostbyname(url.netloc)

        if url_ip not in get_local_ips() and url.netloc != '':
            raise IOError("Data file %s unaccessible from this host" % uri)

    except socket.gaierror:
        LOGGER.warning("Couldn't check file location, running anyway")

    return url.path

# Generic event handler


class EventHandler(pyinotify.ProcessEvent):

    """Handle events with a generic *fun* function.
    """

    def __init__(self, fun, file_to_watch=None, item=None):
        pyinotify.ProcessEvent.__init__(self)
        self._file_to_watch = file_to_watch
        self._item = item
        self._fun = fun

    def process_file(self, pathname):
        '''Process event *pathname*
        '''
        if self._file_to_watch is None:
            self._fun(pathname, self._item)
        elif fnmatch(self._file_to_watch, os.path.basename(pathname)):
            self._fun(pathname, self._item)

    def process_IN_CLOSE_WRITE(self, event):
        """On closing after writing.
        """
        self.process_file(event.pathname)

    def process_IN_CREATE(self, event):
        """On closing after linking.
        """
        try:
            if os.stat(event.pathname).st_nlink > 1:
                self.process_file(event.pathname)
        except OSError:
            return

    def process_IN_MOVED_TO(self, event):
        """On closing after moving.
        """
        self.process_file(event.pathname)


class ConfigWatcher(object):

    """Watch a given config file and run reload_config.
    """

    def __init__(self, config_file, config_item, reload_config):
        mask = (pyinotify.IN_CLOSE_WRITE |
                pyinotify.IN_MOVED_TO |
                pyinotify.IN_CREATE)
        self.config_file = config_file
        self.config_item = config_item
        self.watchman = pyinotify.WatchManager()

        LOGGER.debug("Setting up watcher for %s", config_file)

        self.notifier = \
            pyinotify.ThreadedNotifier(self.watchman,
                                       EventHandler(reload_config,
                                                    os.path.basename(config_file
                                                                     ),
                                                    self.config_item
                                                    )
                                       )
        self.watchman.add_watch(os.path.dirname(config_file), mask)

    def start(self):
        """Start the config watcher.
        """
        LOGGER.info("Start watching %s", self.config_file)
        self.notifier.start()

    def stop(self):
        """Stop the config watcher.
        """
        LOGGER.info("Stop watching %s", self.config_file)
        self.notifier.stop()


def covers(overpass, area_item):
    try:
        area_def = get_area_def(area_item.attrib['id'])
        min_coverage = float(
            area_item.attrib.get('min_coverage', 0))
        min_coverage /= 100.0
        coverage = overpass.area_coverage(area_def)
        if coverage <= min_coverage:
            LOGGER.info("Coverage too small %.1f%% (out of %.1f%%) with %s",
                        coverage * 100, min_coverage * 100,
                        area_item.attrib['name'])
            return False
        else:
            LOGGER.info("Coverage %.1f%% with %s",
                        coverage * 100, area_item.attrib['name'])

    except AttributeError:
        LOGGER.warning("Can't compute area coverage with %s!",
                       area_item.attrib['name'])
    return True


def get_polygons_positions(datas, frequency=1):

    mask = None
    for data in datas:
        if mask is None:
            mask = data.mask
        else:
            mask = np.logical_or(mask, data.mask)

    polygons = []
    polygon_left = []
    polygon_right = []
    count = 0
    last_valid_line = None
    for line in range(mask.shape[0]):
        if np.any(1 - mask[line, :]):
            indices = np.nonzero(1 - mask[line, :])[0]

            if last_valid_line is not None and last_valid_line != line - 1:
                # close the polygon and start a new one.
                last_indices = np.nonzero(1 - mask[last_valid_line, :])[0]
                if count % frequency != 0:
                    polygon_right.append((last_valid_line, last_indices[-1]))
                    polygon_left.append((last_valid_line, last_indices[0]))
                for indice in last_indices[1:-1:frequency]:
                    polygon_left.append((last_valid_line, indice))
                polygon_left.reverse()
                polygons.append(polygon_left + polygon_right)
                polygon_left = []
                polygon_right = []
                count = 0

                for indice in indices[1::frequency]:
                    polygon_right.append((line, indice))
                polygon_left.append((line, indices[0]))

            elif count % frequency == 0:
                polygon_left.append((line, indices[0]))
                polygon_right.append((line, indices[-1]))
            count += 1
            last_valid_line = line

    if (count - 1) % frequency != 0 and last_valid_line is not None:
        polygon_left.append((last_valid_line, indices[0]))
        polygon_right.append((last_valid_line, indices[-1]))

    polygon_left.reverse()
    result = polygon_left + polygon_right
    if result:
        polygons.append(result)

    return polygons


def get_polygons(datas, area, frequency=1):
    polygons = get_polygons_positions(datas, frequency)

    llpolygons = []
    for poly in polygons:
        lons = []
        lats = []
        for line, col in poly:
            lon, lat = area.get_lonlat(line, col)
            lons.append(lon)
            lats.append(lat)
        lons = np.array(lons)
        lats = np.array(lats)
        llpolygons.append(Boundary(lons, lats))

    return llpolygons


def coverage(scene, area):

    shapes = set()
    for channel in scene.channels:
        if channel.is_loaded():
            shapes.add(channel.shape)

    coverages = []

    from trollsched.satpass import Mapper

    for shape in shapes:

        datas = []
        areas = []
        for channel in scene.channels:
            if channel.is_loaded() and channel.shape == shape:
                datas.append(channel.data)
                areas.append(channel.area)

        disk_polys = [poly.contour_poly
                      for poly
                      in get_polygons(datas, areas[0], frequency=100)]

        area_poly = AreaDefBoundary(area, frequency=100).contour_poly

        inter_area = 0

        for poly in disk_polys:
            inter = poly.intersection(area_poly)
            if inter is not None:
                inter_area += inter.area()

        coverages.append(inter_area / area_poly.area())
    try:
        return min(*coverages)
    except TypeError:
        return coverages[0]


def generic_covers(scene, area_item):
    area_def = get_area_def(area_item.attrib['id'])
    min_coverage = float(
        area_item.attrib.get('min_coverage', 0))
    min_coverage /= 100.0
    cov = coverage(scene, area_def)
    if cov <= min_coverage:
        LOGGER.info("Coverage too small %.1f%% (out of %.1f%%) with %s",
                    cov * 100, min_coverage * 100,
                    area_item.attrib['name'])
        return False
    else:
        LOGGER.info("Coverage %.1f%% with %s",
                    cov * 100, area_item.attrib['name'])
        return True


class DataProcessor(object):

    """Process the data.
    """

    def __init__(self):
        self.global_data = None
        self.local_data = None
        self.product_config = None
        self._data_ok = True
        self.writer = DataWriter()
        self.writer.start()

    def stop(self):
        self.writer.stop()

    def create_scene_from_message(self, msg):
        """Parse the message *msg* and return a corresponding MPOP scene.
        """
        if msg.type in ["file", 'collection', 'dataset']:
            return self.create_scene_from_mda(msg.data)

    def create_scene_from_mda(self, mda):
        """Read the metadata *mda* and return a corresponding MPOP scene.
        """
        time_slot = (mda.get('start_time') or
                     mda.get('nominal_time') or
                     mda.get('end_time'))

        # orbit is not given for GEO satellites, use None

        if 'orbit_number' not in mda:
            mda['orbit_number'] = None

        platform = mda["platform_name"]

        LOGGER.info("platform %s time %s",
                    str(platform), str(time_slot))

        if isinstance(mda['sensor'], (list, tuple, set)):
            sensor = mda['sensor'][0]
        else:
            sensor = mda['sensor']

        # Create satellite scene
        global_data = GF.create_scene(satname=str(platform),
                                      satnumber='',
                                      instrument=str(sensor),
                                      time_slot=time_slot,
                                      orbit=mda['orbit_number'],
                                      variant=mda.get('variant', ''))
        LOGGER.debug("Creating scene for satellite %s and time %s",
                     str(platform), str(time_slot))
        if mda['orbit_number'] is not None or mda.get('orbit_type') == "polar":
            global_data.overpass = Pass(platform,
                                        mda['start_time'],
                                        mda['end_time'],
                                        instrument=sensor)

        # Update missing information to global_data.info{}
        # TODO: this should be fixed in mpop.
        global_data.info.update(mda)
        global_data.info['time'] = time_slot

        return global_data

    def save_to_netcdf(self, data, item, params):
        LOGGER.debug("Save full data to netcdf4")
        try:
            params["time_slot"] = data.time_slot
            params["area"] = data.area
            data.add_to_history(
                "Saved as netcdf4/cf by pytroll/mpop.")
            cfscene = CFScene(data)

            self.writer.write(cfscene, item, params)
            LOGGER.info("Sent netcdf/cf scene to writer.")
        except IOError:
            LOGGER.error("Saving unprojected data to NetCDF failed!")
        finally:
            if item.attrib.get("unload_after_saving", "False") == "True":
                loaded_channels = [ch.name
                                   for ch in data.channels]
                LOGGER.info("Unloading data after netcdf4 conversion.")
                data.unload(*loaded_channels)

    def run(self, product_config, msg):
        """Process the data
        """

        if msg.type == "file":
            uri = msg.data['uri']
        elif msg.type == "dataset":
            uri = [mda['uri'] for mda in msg.data['dataset']]
        elif msg.type == 'collection':
            if 'dataset' in msg.data['collection'][0]:
                uri = []
                for dataset in msg.data['collection']:
                    uri.extend([mda['uri'] for mda in dataset['dataset']])
            else:
                uri = [mda['uri'] for mda in msg.data['collection']]
        else:
            LOGGER.warning("Can't run on %s messages", msg.type)
            return
        # TODO collections and collections of datasets

        LOGGER.info('New data available: %s', uri)
        t1a = time.time()

        try:
            filename = check_uri(uri)
            LOGGER.debug(str(filename))
        except IOError as err:
            LOGGER.info(str(err))
            LOGGER.info("Skipping...")
            return

        self.global_data = self.create_scene_from_message(msg)

        self._data_ok = True
        self.product_config = product_config

        area_def_names = self.get_area_def_names()

        for area_item in self.product_config.pl:
            if area_item.tag == "dump":
                self.global_data.load(filename=filename)
                self.save_to_netcdf(self.global_data,
                                    area_item,
                                    self.get_parameters(area_item))

        for group in self.product_config.groups:
            LOGGER.debug("processing %s", str(group))
            area_def_names = self.get_area_def_names(group.data)
            products = []
            skip = []
            skip_group = True
            do_generic_coverage = False

            for area_item in group.data:
                try:
                    if not covers(self.global_data.overpass, area_item):
                        skip.append(area_item)
                        continue
                    else:
                        skip_group = False
                except AttributeError:
                    LOGGER.exception(
                        "Can't compute coverage from unloaded data, continuing")
                    do_generic_coverage = True
                    skip_group = False
                for product in area_item:
                    products.append(product)
            if not products or skip_group:
                continue

            if group.get("unload", "").lower() in ["yes", "true", "1"]:
                loaded_channels = [chn.name for chn
                                   in self.global_data.loaded_channels()]
                self.global_data.unload(*loaded_channels)
                LOGGER.debug("unloading all channels before group %s",
                             group.id)
            try:
                LOGGER.debug("loading channels : %s",
                             str(self.get_req_channels(products)))
                keywords = {"filename": filename,
                            "area_def_names": area_def_names}
                try:
                    keywords["time_interval"] = (msg.data["start_time"],
                                                 msg.data["end_time"])
                except KeyError:
                    pass
                if "resolution" in group.info:
                    keywords["resolution"] = int(group.resolution)
                self.global_data.load(self.get_req_channels(products),
                                      **keywords)
                LOGGER.debug("loaded data : %s", str(self.global_data))
            except IndexError:
                LOGGER.exception("Incomplete or corrupted input data.")
                self._data_ok = False
                break

            for area_item in group.data:
                if area_item in skip:
                    continue
                elif (do_generic_coverage and
                      not generic_covers(self.global_data, area_item)):
                    continue

                # reproject to local domain
                LOGGER.debug(
                    "Projecting data to area " + area_item.attrib['name'])
                try:
                    self.local_data = \
                        self.global_data.project(
                            area_item.attrib["id"],
                            channels=self.get_req_channels(area_item),
                            mode='nearest')
                except ValueError:
                    LOGGER.warning("No data in this area")
                    continue
                except AreaNotFound:
                    LOGGER.warning("Area %s not defined, skipping!",
                                   area_item.attrib['id'])
                    continue

                LOGGER.info(
                    'Data reprojected for area: %s', area_item.attrib['name'])

                # Draw requested images for this area.
                self.draw_images(area_item)

            if group.get("unload", "").lower() in ["yes", "true", "1"]:
                loaded_channels = [chn.name for chn
                                   in self.global_data.loaded_channels()]
                self.global_data.unload(*loaded_channels)
                LOGGER.debug("unloading all channels after group %s",
                             group.id)

        # Wait for the writer to finish
        if self._data_ok:
            LOGGER.debug("Waiting for the files to be saved")
        self.writer.prod_queue.join()
        if self._data_ok:
            LOGGER.debug("All files saved")

            LOGGER.info('File %s processed in %.1f s', uri,
                        time.time() - t1a)

        if not self._data_ok:
            LOGGER.warning("File %s not processed due to "
                           "incomplete/missing/corrupted data." %
                           uri)

        # Release memory
        del self.local_data
        del self.global_data
        self.local_data = None
        self.global_data = None

    def get_req_channels(self, products):
        # Get a list of required channels
        reqs = set()
        for product in products:
            if product.tag == "dump":
                return None
            try:
                composite = getattr(
                    self.global_data.image, product.attrib['id'])
                reqs |= composite.prerequisites
            except AttributeError:
                LOGGER.info("Composite %s not available",
                            product.attrib['id'])
        return reqs

    def get_area_def_names(self, group=None):
        '''Collect and return area definition names from product
        config to a list.
        '''

        pl = group or self.product_config.pl

        def_names = [item.attrib["id"]
                     for item in self.product_config.pl
                     if item.tag == "area"]

        return def_names

    def check_satellite(self, config):
        '''Check if the current configuration allows the use of this
        satellite.
        '''

        # Check the list of valid satellites
        if 'valid_satellite' in config:
            if self.global_data.info['satname'] +\
                    self.global_data.info['satnumber'] not in\
                    config['valid_satellite']:

                info = 'Satellite %s not in list of valid ' \
                    'satellites, skipping product %s.' % \
                    (self.global_data.info['satname'] +
                     self.global_data.info['satnumber'],
                     config['name'])
                LOGGER.info(info)

                return False

        # Check the list of invalid satellites
        if 'invalid_satellite' in config:
            if self.global_data.info['satname'] +\
                    self.global_data.info['satnumber'] in\
                    config['invalid_satellite']:

                info = 'Satellite %s is in the list of invalid ' \
                    'satellites, skipping product %s.' % \
                    (self.global_data.info['satname'] +
                     self.global_data.info['satnumber'],
                     config['name'])
                LOGGER.info(info)

                return False

        return True

    def get_parameters(self, item):
        """Get the parameters for filename sifting.
        """

        params = self.product_config.attrib.copy()

        params.update(self.global_data.info)
        for key, attrib in item.attrib.items():
            params["".join((item.tag, key))] = attrib
        params.update(item.attrib)

        params['aliases'] = self.product_config.aliases.copy()

        return params

    def draw_images(self, area):
        '''Generate images from local data using given area name and
        product definitions.
        '''

        params = self.get_parameters(area)
        # Create images for each color composite
        for product in area:
            params.update(self.get_parameters(product))
            if product.tag == "dump":
                try:
                    self.save_to_netcdf(self.local_data,
                                        product,
                                        params)
                except IOError:
                    LOGGER.error("Saving projected data to NetCDF failed!")
                continue
            elif product.tag != "product":
                continue
            # TODO
            # Check if satellite is one that should be processed
            # if not self.check_satellite(product):
                # Skip this product, if the return value is True
                # continue

            # Check if Sun zenith angle limits match this product
            if 'sunzen_night_minimum' in product.attrib or \
                    'sunzen_day_maximum' in product.attrib:
                if 'sunzen_xy_loc' in product.attrib:
                    xy_loc = [int(x) for x in
                              product.attrib['sunzen_xy_loc'].split(',')]
                    lonlat = None
                else:
                    xy_loc = None
                    if 'sunzen_lonlat' in product.attrib:
                        lonlat = [float(x) for x in
                                  product.attrib['sunzen_lonlat'].split(',')]
                    else:
                        lonlat = None
                if not self.check_sunzen(product.attrib, area_def=get_area_def(area.attrib['id']),
                                         xy_loc=xy_loc, lonlat=lonlat):
                    # If the return value is False, skip this product
                    continue

            try:
                # Check if this combination is defined
                func = getattr(self.local_data.image, product.attrib['id'])
                LOGGER.debug("Generating %s", product.attrib['id'])
                img = func()
                img.info.update(self.global_data.info)
                img.info["product_name"] = product.attrib.get("name",
                                                              product.attrib["id"])
            except AttributeError:
                # Log incorrect product funcion name
                LOGGER.error('Incorrect product id: %s for area %s',
                             product.attrib['id'], area.attrib['name'])
            except KeyError as err:
                # log missing channel
                LOGGER.warning('Missing channel on product %s for area %s: %s',
                               product.attrib['name'], area.attrib['name'], str(err))
            except Exception:
                # log other errors
                LOGGER.exception('Error on product %s for area %s',
                                 product.attrib['name'],
                                 area.attrib['name'])
            else:
                self.writer.write(img, product, params)

        # log and publish completion of this area def
        LOGGER.info('Area %s completed', area.attrib['name'])

    def check_sunzen(self, config, area_def=None, xy_loc=None, lonlat=None,
                     data_name='local_data'):
        '''Check if the data is within Sun zenith angle limits.

        :param config: configuration options for this product
        :type config: dict
        :param area_def: area definition of the data
        :type area_def: areadef
        :param xy_loc: pixel location (2-tuple or 2-element list with x- and y-coordinates) where zenith angle limit is checked
        :type xy_loc: tuple
        :param lonlat: longitude/latitude location (2-tuple or 2-element list with longitude and latitude) where zenith angle limit is checked.
        :type lonlat: tuple
        :param data_name: name of the dataset to get data from
        :type data_name: str

        If both *xy_loc* and *lonlat* are None, image center is used as reference point. *xy_loc* overrides *lonlat*.
        '''

        LOGGER.info('Checking Sun zenith angle limits')
        try:
            data = getattr(self, data_name)
        except AttributeError:
            LOGGER.error('No such data: %s', data_name)
            return False

        if area_def is None and xy_loc is None:
            LOGGER.error('No area definition or pixel location given')
            return False

        # Check availability of coordinates, load if necessary
        if data.area.lons is None:
            LOGGER.debug('Load coordinates for %s', data_name)
            data.area.lons, data.area.lats = data.area.get_lonlats()

        # Check availability of Sun zenith angles, calculate if necessary
        try:
            data.__getattribute__('sun_zen')
        except AttributeError:
            LOGGER.debug('Calculating Sun zenith angles for %s', data_name)
            data.sun_zen = astronomy.sun_zenith_angle(data.time_slot,
                                                      data.area.lons,
                                                      data.area.lats)

        if xy_loc is not None and len(xy_loc) == 2:
            # Use the given xy-location
            x_idx, y_idx = xy_loc
        else:
            if lonlat is not None and len(lonlat) == 2:
                # Find the closest pixel to the given coordinates
                dists = (data.area.lons - lonlat[0]) ** 2 + \
                    (data.area.lats - lonlat[1]) ** 2
                y_idx, x_idx = np.where(dists == np.min(dists))
                y_idx, x_idx = int(y_idx), int(x_idx)
            else:
                # Use image center
                y_idx = int(area_def.y_size / 2)
                x_idx = int(area_def.x_size / 2)

        # Check if Sun is too low (day-only products)
        try:
            LOGGER.debug('Checking Sun zenith-angle limit at '
                         '(lon, lat) %3.1f, %3.1f (x, y: %d, %d)',
                         data.area.lons[y_idx, x_idx],
                         data.area.lats[y_idx, x_idx],
                         x_idx, y_idx)

            if float(config['sunzen_day_maximum']) < \
                    data.sun_zen[y_idx, x_idx]:
                LOGGER.info('Sun too low for day-time product.')
                return False
        except KeyError:
            pass

        # Check if Sun is too high (night-only products)
        try:
            if float(config['sunzen_night_minimum']) > \
                    data.sun_zen[y_idx, x_idx]:
                LOGGER.info('Sun too high for night-time '
                            'product.')
                return False
        except KeyError:
            pass

        return True


def _create_message(obj, filename, uri, params):
    to_send = obj.info.copy()

    for key in ['collection', 'dataset']:
        if key in to_send:
            del to_send[key]

    to_send["nominal_time"] = getattr(obj, "time_slot",
                                      params.get("time_slot"))
    area = getattr(obj, "area", params.get("area"))

    to_send["area"] = {}
    try:
        to_send["area"]["name"] = area.name
        to_send["area"]["id"] = area.area_id
        try:
            to_send["area"]["proj_id"] = area.proj_id
            to_send["area"]["proj4"] = area.proj4_string
            to_send["area"]["area_extent"] = area.area_extent
            to_send["area"]["shape"] = area.x_size, obj.area.y_size
        except AttributeError:
            pass
    except AttributeError:
        del to_send["area"]

    # FIXME: fishy: what if the uri already has a scheme ?
    to_send["uri"] = urlunsplit(("file", "", uri, "", ""))
    to_send["uid"] = os.path.basename(filename)
    # we should have more info on format...
    fformat = os.path.splitext(filename)[1][1:]
    if fformat.startswith("tif"):
        fformat = "GeoTIFF"
    elif fformat.startswith("png"):
        fformat = "PNG"
    elif fformat.startswith("jp"):
        fformat = "JPEG"
    elif fformat.startswith("nc"):
        fformat = "NetCDF"
    to_send["type"] = fformat
    if fformat != "NetCDF":
        to_send["format"] = "raster"
        to_send["data_processing_level"] = "2"
        to_send["product_name"] = obj.info["product_name"]
    else:
        to_send["format"] = "CF"
        to_send["data_processing_level"] = "1b"
        to_send["product_name"] = "dump"

    subject = "/".join(("",
                        to_send["format"],
                        to_send["data_processing_level"]))

    msg = Message(subject,
                  "file",
                  to_send)
    return msg


def link_or_copy(src, dst):
    if src == dst:
        LOGGER.warning("Trying to copy a file over itself: %s", src)
        return
    try:
        os.link(src, dst)
    except OSError as err:
        if err.errno not in [errno.EXDEV]:
            LOGGER.exception("Could not link: %s -> %s", src, dst)
            return
        try:
            shutil.copy(src, dst)
        except shutil.Error:
            LOGGER.exception("Something went wrong in copying a file")
        except IOError as err:
            LOGGER.info(str(err))
            LOGGER.exception("Could not copy: %s -> %s", src, dst)


def thumbnail(filename, thname, size, fformat):
    from PIL import Image
    im = Image.open(filename)
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(thname, fformat)


def hash_color(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#':
        colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError("input #%s is not in #RRGGBB format" % colorstring)
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)


class DataWriter(Thread):

    """Writes data to disk.

    This is separate from the DataProcessor since it takes IO time and we don't
    want to block processing.
    """

    def __init__(self):
        Thread.__init__(self)
        self.prod_queue = Queue.Queue()
        self._loop = True

    def run(self):
        """Run the thread.
        """
        with Publish("l2producer") as pub:
            while self._loop:
                try:
                    obj, file_items, params = self.prod_queue.get(True, 1)
                except Queue.Empty:
                    continue
                try:
                    # Sort the file items in categories, to allow copying
                    # similar ones.
                    sorted_items = {}
                    for item in file_items:
                        attrib = item.attrib.copy()
                        for key in ["output_dir",
                                    "thumbnail_name",
                                    "thumbnail_size"]:
                            if key in attrib:
                                del attrib[key]
                        if 'format' not in attrib:
                            attrib.setdefault('format',
                                              os.path.splitext(item.text)[1][1:])

                        key = tuple(sorted(attrib.items()))
                        sorted_items.setdefault(key, []).append(item)

                    local_params = params.copy()
                    local_aliases = local_params['aliases']
                    for key, aliases in local_aliases.items():
                        if key in local_params:
                            local_params[key] = aliases.get(params[key],
                                                            params[key])
                    for item, copies in sorted_items.items():
                        attrib = dict(item)
                        if attrib.get("overlay", "").startswith("#"):
                            obj.add_overlay(hash_color(attrib.get("overlay")))
                        elif len(attrib.get("overlay", "")) > 0:
                            LOGGER.debug("Adding overlay from config file")
                            obj.add_overlay_config(attrib["overlay"])
                        fformat = attrib.get("format")

                        # Actually save the data to disk.
                        saved = False
                        for copy in copies:
                            output_dir = copy.attrib.get("output_dir",
                                                         params["output_dir"])
                            fname = compose(os.path.join(output_dir, copy.text),
                                            local_params)
                            if not saved:
                                obj.save(fname,
                                         fformat=fformat,
                                         compression=copy.attrib.get("compression", 6))
                                LOGGER.info("Saved %s to %s", str(obj), fname)
                                saved = fname
                            else:
                                link_or_copy(saved, fname)
                                saved = fname

                            if ("thumbnail_name" in copy.attrib and
                                    "thumbnail_size" in copy.attrib):
                                thsize = [int(val) for val
                                          in copy.attrib["thumbnail_size"].split("x")]
                                copy.attrib["thumbnail_size"] = thsize
                                thname = compose(os.path.join(output_dir,
                                                              copy.attrib["thumbnail_name"]),
                                                 local_params)
                                copy.attrib["thumbnail_name"] = thname
                                thumbnail(fname, thname, thsize, fformat)

                            msg = _create_message(obj, os.path.basename(fname),
                                                  fname, params)
                            pub.send(str(msg))
                            LOGGER.debug("Sent message %s", str(msg))
                except:
                    for item in file_items:
                        if "thumbnail_size" in item.attrib:
                            item.attrib["thumbnail_size"] = str(
                                item.attrib["thumbnail_size"])
                    LOGGER.exception("Something wrong happened saving %s to %s",
                                     str(obj),
                                     str([tostring(item)
                                          for item in file_items]))
                finally:
                    self.prod_queue.task_done()

    def write(self, obj, item, params):
        '''Write to queue.
        '''
        self.prod_queue.put((obj, list(item), params.copy()))

    def stop(self):
        '''Stop the data writer.
        '''
        LOGGER.info("stopping data writer")
        self._loop = False


class Trollduction(object):

    """Trollduction takes in messages and generates DataProcessor jobs.
    """

    def __init__(self, config, managed=True):
        LOGGER.debug("Trollduction starting now")

        self.td_config = None
        self.product_config = None
        self.listener = None

        self.global_data = None
        self.local_data = None

        self._loop = True
        self.thr = None
        self.data_processor = DataProcessor()
        self.config_watcher = None

        # read everything from the Trollduction config file
        try:
            self.update_td_config_from_file(config['config_file'],
                                            config['config_item'])
            if not managed:
                self.config_watcher = \
                    ConfigWatcher(config['config_file'],
                                  self.update_td_config_from_file)
                self.config_watcher.start()

        except AttributeError:
            self.td_config = config
            self.update_td_config()

    def update_td_config_from_file(self, fname, config_item=None):
        '''Read Trollduction config file and use the new parameters.
        '''
        self.td_config = helper_functions.read_config_file(fname, config_item)
        self.update_td_config()

    def update_td_config(self):
        '''Setup Trollduction with the loaded configuration.
        '''

        LOGGER.info('Trollduction configuration read successfully.')

        # Initialize/restart listener
        if self.listener is None:
            self.listener = \
                ListenerContainer(topics=self.td_config['topics'].split(','))
#            self.listener = ListenerContainer()
            LOGGER.info("Listener started")
        else:
            #            self.listener.restart_listener('file')
            self.listener.restart_listener(self.td_config['topics'].split(','))
            LOGGER.info("Listener restarted")

        try:
            self.update_product_config(self.td_config['product_config_file'],
                                       self.td_config['config_item'])
        except KeyError:
            LOGGER.exception("Key 'product_config_file' or 'config_item' is "
                             "missing from Trollduction config")

    def update_product_config(self, fname, config_item):
        '''Update area definitions, associated product names, output
        filename prototypes and other relevant information from the
        given file.
        '''
        import xml_read
        self.product_config = xml_read.ProductList(fname)

        # product_config = \
        #    helper_functions.read_config_file(fname,
        # config_item=config_item)

        # add checks, or do we just assume the config to be valid at
        # this point?
        # self.product_config = product_config
        if self.td_config['product_config_file'] != fname:
            self.td_config['product_config_file'] = fname

        LOGGER.info('Product config read from %s', fname)

    def cleanup(self):
        '''Cleanup Trollduction before shutdown.
        '''

        # more cleanup needed?
        if self._loop:
            LOGGER.info('Shutting down Trollduction.')
            self._loop = False
            self.data_processor.stop()
            if self.config_watcher is not None:
                self.config_watcher.stop()
            if self.listener is not None:
                self.listener.stop()

    def stop(self):
        """Stop running.
        """
        self.cleanup()

    def shutdown(self):
        '''Shutdown trollduction.
        '''
        self.stop()

    def run_single(self):
        """Run trollduction.
        """
        try:
            while self._loop:
                # wait for new messages
                try:
                    msg = self.listener.queue.get(True, 5)
                except KeyboardInterrupt:
                    self.stop()
                    raise
                except Queue.Empty:
                    continue
                LOGGER.debug(str(msg))
                if isinstance(msg.data['sensor'], (list, tuple, set)):
                    sensors = set(msg.data['sensor'])
                else:
                    sensors = set((msg.data['sensor'], ))
                if (msg.type in ["file", 'collection', 'dataset'] and
                        sensors.intersection(self.td_config['instruments'].split(','))):
                    self.update_product_config(self.td_config['product_config_file'],
                                               self.td_config['config_item'])
                    self.data_processor.run(self.product_config, msg)

        finally:
            self.shutdown()
