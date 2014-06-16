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

'''Old version of Trollduction module, used for testing new stuff
'''

from listener import ListenerContainer
from mpop.satellites import GenericFactory as GF
import datetime as dt
import time
from mpop.projector import get_area_def
import sys
from pyorbital import astronomy
import numpy as np
import os
import Queue
import logging
import logging.handlers
from helper_functions import read_config_file

LOGGER = logging.getLogger(__name__)

class OldTrollduction(object):
    '''Trollduction class for easy generation chain setup
    '''

    def __init__(self, td_config_file=None):
        '''Init Trollduction instance
        '''

        self.td_config = None
        self.product_config = None
        self.listener = None

        self.global_data = None
        self.local_data = None

        self._loop = True

        # read everything from the Trollduction config file
        if td_config_file is not None:
            self.update_td_config(td_config_file)


    def update_td_config(self, fname=None):
        '''Update Trollduction configuration from the given file.
        '''

        if fname is not None:
            self.td_config = read_config_file(fname)
        else:
            return

        LOGGER.info('Trollduction configuration read successfully.')

        # Initialize/restart listener
        try:
            if self.listener is None:
                self.listener = ListenerContainer(\
                    data_type_list=self.td_config['listener_tag'])
                LOGGER.info("Listener started")
            else:
                self.listener.restart_listener(self.td_config['listener_tag'])
                LOGGER.info("Listener restarted")
        except KeyError:
            LOGGER.critical("Key <listener_tag> is missing from"
                            " Trollduction config: %s", fname)

        try:
            self.update_product_config(\
                fname=self.td_config['product_config_file'])
        except KeyError:
            LOGGER.critical("Key <product_config_file> is missing "
                            "from Trollduction config: %s", fname)


    def update_product_config(self, fname=None):
        '''Update area definitions, associated product names, output
        filename prototypes and other relevant information from the
        given file.
        '''

        if fname is not None:
            product_config = read_config_file(fname)
        else:
            product_config = None

        # add checks, or do we just assume the config to be valid at
        # this point?
        self.product_config = product_config
        if self.td_config['product_config_file'] != fname:
            self.td_config['product_config_file'] = fname

        LOGGER.info('New product config read from %s', fname)


    def cleanup(self):
        '''Cleanup Trollduction before shutdown.
        '''

        LOGGER.info('Shutting down Trollduction.')

        # more cleanup needed?
        self._loop = False

        if self.listener is not None:
            self.listener.stop()

    def shutdown(self):
        '''Shutdown trollduction.
        '''
        self.cleanup()
        sys.exit()


    def run_single(self):
        '''Run image production without threading.
        '''
        # TODO: Get relevant preprocessing function for this
        #   production chain type: single/multi, or
        #   swath, geo, granule, global_polar, global_geo, global_mixed
        # That is, gatherer for the multi-image/multi-granule types
        # preproc_func = getattr(preprocessing, self.production_type)

        while self._loop:
            # wait for new messages
            try:
                msg = self.listener.queue.get(True, 5)
            except KeyboardInterrupt:
                LOGGER.info('Keyboard interrupt detected')
                self.cleanup()
                raise
            except Queue.Empty:
                continue

            # Skip self published messages
            if '/Message' in msg.subject:
                continue

            LOGGER.info('New message received ' + str(msg))

            # shutdown trollduction
            if '/StopTrollduction' in msg.subject:
                LOGGER.info('Shutting down Trollduction on request')
                self.cleanup()
                break # this should shutdown Trollduction
            # update trollduction config
            elif '/NewTrollductionConfig' in msg.subject:
                LOGGER.info('Reading new Trollduction config')
                self.update_td_config(msg.data)
            # update product lists
            elif '/NewProductConfig' in msg.subject:
                LOGGER.info('Reading new product config')
                self.update_product_config(msg.data)
            # process new file
            elif '/NewFileArrived' in msg.subject:
                LOGGER.info('New data available: %s', msg.data['uri'])

                time_slot = dt.datetime(int(msg.data['year']),
                                        int(msg.data['month']),
                                        int(msg.data['day']),
                                        int(msg.data['hour']),
                                        int(msg.data['minute']))

                # orbit is empty string for meteosat, change it to None
                if msg.data['orbit'] == '':
                    msg.data['orbit'] = None

                t1a = time.time()

                # Create satellite scene
                self.global_data = GF.create_scene(\
                    satname=str(msg.data['satellite']),
                    satnumber=str(msg.data['satnumber']),
                    instrument=str(msg.data['instrument']),
                    time_slot=time_slot,
                    orbit=str(msg.data['orbit']))

                # Update missing information to global_data.info{}
                self.global_data.info['satname'] = msg.data['satellite']
                self.global_data.info['satnumber'] = msg.data['satnumber']
                self.global_data.info['instrument'] = msg.data['instrument']
                self.global_data.info['orbit'] = msg.data['orbit']

                area_def_names = self.get_area_def_names()

                # Save full unprojected data to netcdf4
                if 'netcdf_file' in self.product_config['common']:
                    self.global_data.load()
                    self.write_netcdf(data_name='global_data', unload=True)

                # Make images for each area
                for area in self.product_config['area']:

                    # Check if satellite is one that should be processed
                    if not self.check_satellite(area):
                        # if return value is False, skip this loop step
                        continue

                    t1b = time.time()

                    # Check which channels are needed. Unload
                    # unnecessary channels and load those that are not
                    # already available.  If NetCDF4 data is to be
                    # saved, use all data, otherwise unload
                    # unnecessary channels.
                    if 'netcdf_file' in area:
                        LOGGER.info('Load all channels for saving.')
                        try:
                            if msg.data['orbit'] is not None:
                                raise TypeError
                            self.global_data.load(area_def_names=\
                                                      area_def_names)
                        except TypeError:
                            # load all data if area_def_names keyword
                            # isn't available in instrument reader or
                            # the data is swath based
                            LOGGER.info('Loading full swath data')
                            self.global_data.load()
                    else:
                        LOGGER.info('Loading required channels.')
                        self.load_unload_channels(area['product'],
                                                  area_def_names=\
                                                      area_def_names)

                    # reproject to local domain
                    LOGGER.info('Reprojecting data for area: %s' % area['name'])
                    try:
                        self.local_data = \
                            self.global_data.project(area['definition'],
                                                     mode='nearest')
                    except ValueError:
                        LOGGER.warning("No data in this area")
                        continue

                    # Save projected data to netcdf4
                    if 'netcdf_file' in area:
                        self.write_netcdf('local_data', area=area)

                    LOGGER.info('Data reprojected for area: %s', area['name'])

                    # Draw requested images for this area.
                    self.draw_images(area)

                    LOGGER.info('Area processed in %.1f s', (time.time()-t1b))

                # Release memory
                self.local_data = None
                self.global_data = None

                LOGGER.info('File %s processed in %.1f s',
                            msg.data['uri'],
                            time.time() - t1a)
            else:
                # Unhandled message types end up here
                # No need to log these?
                pass


    def load_unload_channels(self, products, area_def_names=None):
        '''Load channel data required for the given list of *products*
        for the given area definition name(s) *area_def_names*.
        Unload channels that are not needed.
        '''

        loaded_channels = []
        required_channels = []
        wavelengths = []

        # Get information which channels are loaded
        for chan in self.global_data.channels:
            required_channels.append(False)
            wavelengths.append(chan.wavelength_range)
            if chan.is_loaded():
                loaded_channels.append(True)
            else:
                loaded_channels.append(False)

        # Get a list of required channels
        for product in products:
            reqs = eval('self.global_data.image.'+ \
                            product['composite']+'.prerequisites')
            for req in reqs:
                for i in range(len(self.global_data.channels)):
                    if req >= np.min(wavelengths[i]) and \
                            req <= np.max(wavelengths[i]):
                        required_channels[i] = True
                        break

        to_load = []
        to_unload = []
        for i in range(len(self.global_data.channels)):
            if required_channels[i] and not loaded_channels[i]:
                to_load.append(self.global_data.channels[i].name)
            if not required_channels[i] and loaded_channels[i]:
                to_unload.append(self.global_data.channels[i].name)

        LOGGER.debug('Channels to unload: %s', ', '.join(to_unload))
        LOGGER.debug('Channels to load: %s', ', '.join(to_load))

        self.global_data.unload(*to_unload)
        
        try:
            self.global_data.load(to_load, area_def_names=area_def_names)
        except TypeError:
            LOGGER.info('Loading full data')
            # load whole area if area_def_names keywoard isn't available
            # in the instrument reader
            self.global_data.load(to_load)


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
                    (self.global_data.info['satname'] + \
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
                    (self.global_data.info['satname'] + \
                         self.global_data.info['satnumber'],
                     config['name'])
                LOGGER.info(info)

                return False

        return True


    def draw_images(self, area):
        '''Generate images from local data using given area name and
        product definitions.
        '''

        # Create images for each color composite
        for product in area['product']:

            # Check if satellite is one that should be processed
            if not self.check_satellite(product):
                # Skip this product, if the return value is True
                continue

            # Check if Sun zenith angle limits match this product
            if 'sunzen_night_minimum' in product or \
                    'sunzen_day_maximum' in product:
                if 'sunzen_xy_loc' in product:
                    xy_loc = [int(x) for x in \
                                  product['sunzen_xy_loc'].split(',')]
                    lonlat = None
                else:
                    xy_loc = None
                    if 'sunzen_lonlat' in product:
                        lonlat = [float(x) for x in \
                                      product['sunzen_lonlat'].split(',')]
                    else:
                        lonlat = None
                if not self.check_sunzen(product, area_def=\
                                             get_area_def(area['definition']),
                                         xy_loc=xy_loc, lonlat=lonlat):
                    # If the return value is False, skip this product
                    continue

            # Parse image filename
            fname = self.parse_filename(area, product)

            try:
                # Check if this combination is defined
                func = getattr(self.local_data.image, product['composite'])
                img = func()
                img.save(fname)

                LOGGER.info('Image %s saved.', fname)

            except AttributeError:
                # Log incorrect product funcion name
                LOGGER.error('Incorrect product name: %s for area %s',
                             product['name'], area['name'])
            except KeyError:
                # log missing channel
                LOGGER.warning('Missing channel on product %s for area %s',
                               product['name'], area['name'])
            except:
                _, val = sys.exc_info()[0]
                # log other errors
                LOGGER.error('Error %s on product %s for area %s',
                             val.message,
                             product['name'],
                             area['name'])

        # log and publish completion of this area def
        LOGGER.info('Area %s completed', area['name'])


    def write_netcdf(self, data_name='global_data', area=None, unload=False):
        '''Write the data as netCDF4.
        '''

        LOGGER.info('Saving data to netCDF4')
        try:
            data = getattr(self, data_name)
        except AttributeError:
            LOGGER.info('No such data: %s', data_name)
            return

        # parse filename
        fname = self.parse_filename(area=area, fname_key='netcdf_file')
        LOGGER.info('netCDF4 filename is %s' % fname)

        # Load all the data
        data.load()
        # Save the data
        data.save(fname, to_format='netcdf4')

        if unload:
            loaded_channels = [ch.name for ch in data.channels]
            data.unload(*loaded_channels)

        LOGGER.info('Data saved to %s', fname)


    def parse_filename(self, area=None, product=None, fname_key='filename'):
        '''Parse filename.  Parameter *area* is for area-level
        configuration dictionary, *product* for product-level
        configuration dictionary.  Parameter *fname_key* tells which
        dictionary key holds the filename pattern.
        '''
        try:
            out_dir = product['output_dir']
        except (KeyError, TypeError):
            try:
                out_dir = area['output_dir']
            except (KeyError, TypeError):
                out_dir = self.product_config['common']['output_dir']

        try:
            fname = product[fname_key]
        except (KeyError, TypeError):
            try:
                fname = area[fname_key]
            except (KeyError, TypeError):
                fname = self.product_config['common'][fname_key]

        fname = os.path.join(out_dir, fname)

        try:
            time_slot = self.local_data.time_slot
        except AttributeError:
            time_slot = self.global_data.time_slot
        fname = fname.replace('%Y', '%04d' % time_slot.year)
        fname = fname.replace('%m', '%02d' % time_slot.month)
        fname = fname.replace('%d', '%02d' % time_slot.day)
        fname = fname.replace('%H', '%02d' % time_slot.hour)
        fname = fname.replace('%M', '%02d' % time_slot.minute)
        if area is not None:
            fname = fname.replace('%(areaname)', area['name'])
        if product is not None:
            fname = fname.replace('%(composite)', product['name'])
        fname = fname.replace('%(satellite)',
                              self.global_data.info['satname'] + \
                                  self.global_data.info['satnumber'])
        if self.global_data.info['orbit'] is not None:
            fname = fname.replace('%(orbit)', self.global_data.info['orbit'])
        fname = fname.replace('%(instrument)',
                              self.global_data.info['instrument'])
        fname = fname.replace('%(ending)', 'png')

        return fname


    def check_sunzen(self, config, area_def=None, xy_loc=None, lonlat=None,
                     data_name='local_data'):
        '''Check if the data is within Sun zenith angle limits.
        *config*: configuration options for this product
        *area_def*: area definition of the data
        *xy_loc*: pixel location (2-tuple or 2-element list with x-
                  and y-coordinates) where zenith angle limit is checked
        *lonlat*: longitude/latitude location (2-tuple or 2-element
                  list with longitude and latitude) where zenith angle
                  limit is checked.
        *data_name*: name of the dataset to get data from

        If both *xy_loc* and *lonlat* are None, image center is used
        as reference point. *xy_loc* overrides *lonlat*.
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
                dists = (data.area.lons - lonlat[0])**2 + \
                    (data.area.lats - lonlat[1])**2
                y_idx, x_idx = np.where(dists == np.min(dists))
                y_idx, x_idx = int(y_idx), int(x_idx)
            else:
                # Use image center
                y_idx = int(area_def.y_size/2)
                x_idx = int(area_def.x_size/2)

        # Check if Sun is too low (day-only products)
        try:
            LOGGER.debug('Checking Sun zenith-angle limit at '
                         '(lon, lat) %3.1f, %3.1f (x, y: %d, %d)',
                         data.area.lons[y_idx, x_idx],
                         data.area.lats[y_idx, x_idx],
                         x_idx, y_idx)

            if float(config['sunzen_day_maximum']) < \
                    data.sun_zen[y_idx, x_idx]:
                LOGGER.info('Sun too low for day-time '
                                            'product.')
                return False
        except KeyError:
            pass

        # Check if Sun is too high (night-only products)
        try:
            if float(config['sunzen_night_minimum']) > \
                    data.sun_zen[y_idx, x_idx]:
                LOGGER.info('Sun too low for night-time '
                                            'product.')
                return False
        except KeyError:
            pass

        return True


    def get_area_def_names(self):
        '''Collect and return area definition names from product
        config to a list.
        '''

        def_names = [area['definition'] for area in self.product_config['area']]

        return def_names

    
