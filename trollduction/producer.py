# -*- coding: utf-8 -*-
#
# Copyright (c) 2014
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

from listener import ListenerContainer
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
import helper_functions
from trollsift import compose
from urlparse import urlparse
import socket
from mpop.satout.cfscene import CFScene

LOGGER = logging.getLogger(__name__)

# Config watcher stuff

import pyinotify

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

    def create_scene_from_message(self, msg):
        """Parse the message *msg* and return a corresponding MPOP scene.
        """
        time_slot = (msg.data.get('time') or
                     msg.data.get('start_time') or
                     msg.data.get('nominal_time'))

        # orbit is not given for GEO satellites, use None

        if 'orbit_number' not in msg.data:
            msg.data['orbit_number'] = None

        platform = (msg.data.get('platform') or
                    msg.data.get('satellite').split()[0]).lower()
        satnumber = (msg.data.get('satnumber') or
                     msg.data.get('satellite').split()[1])
        try:
            satnumber = int(satnumber)
        except ValueError:
            satnumber = satnumber.lower()
        LOGGER.info("platform %s, number %s", str(platform), str(satnumber))

        # Create satellite scene
        global_data = GF.create_scene(satname=str(platform),
                                      satnumber=str(satnumber),
                                      instrument=str(msg.data['instrument']),
                                      time_slot=time_slot,
                                      orbit=str(msg.data['orbit_number']))

        # Update missing information to global_data.info{}
        # TODO: this should be fixed in mpop.
        global_data.info['time'] = time_slot
        global_data.info['platform'] = platform
        global_data.info['satnumber'] = satnumber
        global_data.info['instrument'] = msg.data['instrument']
        global_data.info['orbit_number'] = msg.data['orbit_number']

        return global_data

    @staticmethod
    def check_uri(uri):
        """Check that the provided *uri* is on the local host and return the
        file path.
        """
        url = urlparse(uri)
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            url_ip = socket.gethostbyname(url.netloc)

            if url_ip != local_ip and url.netloc != '':
                raise IOError("Data file %s unaccessible from this host" % uri)

        except socket.gaierror:
            LOGGER.warning("Couldn't check file location, running anyway")

        return url.path

    def save_to_netcdf(self, data, item, params):
        LOGGER.debug("Save full data to netcdf4")
        try:
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

        uri = msg.data['uri']

        LOGGER.info('New data available: %s', uri)
        t1a = time.time()

        try:
            filename = self.check_uri(uri)
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
            if area_item.tag == "area":
                # Make images for an area

                # TODO
                # Check if satellite is one that should be processed
                # if not self.check_satellite(area):
                    # if return value is False, skip this loop step
                    # continue

                t1b = time.time()

                dump = False

                for product_item in area_item:
                    if product_item.tag == "dump":
                        dump = product_item
                        break

                # Check which channels are needed. Unload unnecessary
                # channels and load those that are not already available.
                # If NetCDF4 data is to be saved, use all data, otherwise
                # unload unnecessary channels.
                if dump:
                    # TODO
                    LOGGER.info('Load all channels for dump.')
                    try:
                        if msg.data['orbit_number'] is not None:
                            raise TypeError
                        try:
                            self.global_data.load(filename=filename,
                                                  area_def_names=area_def_names)
                        except IndexError:
                            LOGGER.error("Incomplete or corrupted input data.")
                            self._data_ok = False
                            break
                    except TypeError:
                        # load all data if area_def_names keyword isn't
                        # available in instrument reader or the data is
                        # swath based
                        LOGGER.info('Loading full swath data')
                        try:
                            self.global_data.load(filename=filename)
                        except IndexError:
                            LOGGER.error("Incomplete or corrupted input data.")
                            self._data_ok = False
                            break
                else:
                    LOGGER.info('Loading required channels.')
                    try:
                        self.load_unload_channels(area_item,
                                                  area_def_names=area_def_names,
                                                  filename=filename)
                    except IndexError:
                        LOGGER.error("Incomplete or corrupted input data.")
                        self._data_ok = False
                        break

                # reproject to local domain
                LOGGER.debug(
                    "Projecting data to area " + area_item.attrib['name'])
                try:
                    self.local_data = \
                        self.global_data.project(area_item.attrib["id"],
                                                 mode='nearest')
                except ValueError:
                    LOGGER.warning("No data in this area")
                    continue

                LOGGER.info(
                    'Data reprojected for area: %s', area_item.attrib['name'])

                # Draw requested images for this area.
                self.draw_images(area_item)

                LOGGER.info('Area processed in %.1f s', (time.time() - t1b))

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

    def load_unload_channels(self, products, area_def_names=None, filename=None):
        '''Load channel data required for the given list of *products*
        for the given area definition name(s) *area_def_names*.
        Unload channels that are not needed.
        '''

        loaded_channels = []
        required_channels = []
        wavelengths = []
        chan_names = []

        # Get information which channels are loaded
        for chan in self.global_data.channels:
            required_channels.append(False)
            wavelengths.append(chan.wavelength_range)
            chan_names.append(chan.name)
            if chan.is_loaded():
                loaded_channels.append(True)
            else:
                loaded_channels.append(False)

        # Get a list of required channels
        reqs = set()
        for product in products:
            if product.tag != "product":
                continue
            composite = getattr(self.global_data.image, product.attrib['id'])
            reqs |= composite.prerequisites

        LOGGER.debug('Channels: %s', str(self.global_data))

        to_load = set()
        to_unload = set([chn.name for chn in self.global_data.channels])

        for chn in reqs:
            to_load |= set([self.global_data[chn].name])
            to_unload -= set([self.global_data[chn].name])

        LOGGER.debug('Channels to unload: %s', ', '.join(to_unload))
        LOGGER.debug('Channels to load: %s', ', '.join(to_load))

        self.global_data.unload(*to_unload)

        try:
            self.global_data.load(to_load, area_def_names=area_def_names,
                                  filename=filename)
        except TypeError:
            LOGGER.info("Loading full data")
            # load whole area if area_def_names keywoard isn't
            # available in the instrument reader
            self.global_data.load(to_load, filename=filename)

    def get_area_def_names(self):
        '''Collect and return area definition names from product
        config to a list.
        '''

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
                img = func()

            except AttributeError:
                # Log incorrect product funcion name
                LOGGER.error('Incorrect product name: %s for area %s',
                             product.attrib['name'], area.attrib['name'])
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
        while self._loop:
            try:
                obj, file_items, params = self.prod_queue.get(True, 1)
            except Queue.Empty:
                pass
            else:
                for item in file_items:
                    fname = os.path.join(params["output_dir"],
                                         compose(item.text, params))
                    obj.save(fname)
                    LOGGER.info("Saved %s to %s", str(obj), fname)
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
                ListenerContainer(topic=self.td_config['topic'])
#            self.listener = ListenerContainer()
            LOGGER.info("Listener started")
        else:
            #            self.listener.restart_listener('file')
            self.listener.restart_listener(self.td_config['topic'])
            LOGGER.info("Listener restarted")

        try:
            self.update_product_config(self.td_config['product_config_file'],
                                       self.td_config['config_item'])
        except KeyError:
            print ""
            print self.td_config
            print ""
            LOGGER.critical("Key 'product_config_file' or 'config_item' is "
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
        #self.product_config = product_config
        if self.td_config['product_config_file'] != fname:
            self.td_config['product_config_file'] = fname

        LOGGER.info('Product config read from %s', fname)

    def cleanup(self):
        '''Cleanup Trollduction before shutdown.
        '''

        LOGGER.info('Shutting down Trollduction.')

        # more cleanup needed?
        self._loop = False
        self.data_processor.writer.stop()
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
        while self._loop:
            # wait for new messages
            try:
                msg = self.listener.queue.get(True, 5)
            except KeyboardInterrupt:
                self.stop()
                raise
            except Queue.Empty:
                continue

            # For 'file' type messages, update product config and run
            # production
            if msg.type == "file" and msg.data["instrument"] == self.td_config['instrument']:
                self.update_product_config(self.td_config['product_config_file'],
                                           self.td_config['config_item'])
                self.data_processor.run(self.product_config, msg)

#            else:
#                LOGGER.debug("Message type was %s" % msg.type)
