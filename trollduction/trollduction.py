'''Trollduction module
'''
# -*- coding: utf-8 -*-

# Copyright (c) 2014

# Author(s):

#   Panu Lahtinen <panu.lahtinen@fmi.fi>

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

from multiprocessing import Pipe
from threading import Thread
from listener import Listener
#from publisher import Publisher
#from logger import Logger
from mpop.satellites import GenericFactory as GF
import datetime as dt
import time
from mpop.projector import get_area_def
import sys

class Trollduction(object):
    '''Trollduction class for easy generation chain setup
    '''

    def __init__(self, td_config_file=None):
        '''Init Trollduction instance
        '''

        # configuration file for the Trollduction instance
        self.td_config_file = td_config_file

        # read everything from the Trollduction config file
        if td_config_file is not None:
            self.update_td_config()

        # otherwise set empty placeholders
        else:
            self.product_list_file = None
            self.area_def_names = None
            # product list is a dict with area def names as keys and
            # product names as value arrays
            # eg. {'euro4km': ['green_snow', 'overview']}
            self.product_list = None
            self.listener = None
            self.listener_thread = None
            self.listener_parent_conn = None
            self.listener_child_conn = None
#            self.publisher = None
#            self.logger = None
            self.image_filename_template = None
            self.image_output_dir = None
            # single swath or MSG disc: 'single'
            # multiple granules or GEO images: 'multi'
            self.production_type = None
#            self.pool = None
#            self.pool_size = None
#            self.loaded_channels = []

    def update_td_config(self, fname=None):
        '''Update Trollduction configuration from the given file.
        '''

        # TODO: add checks what has changed
        # TODO: restart relevant parts

        if fname is not None:
            self.td_config_file = fname
            td_config = read_config_file(fname)
        elif self.td_config_file is not None:
            td_config = read_config_file(self.td_config_file)
        else:
            return
            
        keys = td_config.keys()

        if 'listener' in keys:
            # TODO: check if changed
            self.restart_listener(td_config['listener']['address_list'], 
                                  td_config['listener']['msg_type_list'])

        '''
        if 'parallel' in keys:
            if 'num_processes' in keys:
                # TODO: check if changed
                self.init_pool(num_processes=td_config['num_processes'])
            else:
                self.init_pool()
        '''

        if '' in keys:
            # TODO: check if changed
            pass


    def update_product_config(self, fname=None):
        '''Update area definitions, associated product names, output
        filename prototypes and other relevant information from the
        given file.
        '''
        if fname is not None:
            self.product_config_file = fname
            product_config = read_config_file(fname)
        elif self.product_config_file is not None:
            product_config = read_config_file(self.product_config_file)
        else:
            product_config = None

        # add checks, or do we just assume the config to be valid at
        # this point?
        self.product_config = product_config


    def read_config_file(self, fname=None):
        '''Read config file to dictionary.
        '''

        # TODO: check validity
        # TODO: read config, parse to dict, logging

        if fname is None:
            return None
        else:
            # TODO: read config
            pass


    def init_listener(self, data_type_list):
        '''Initialise listener that receives messages about new files
        to be processed, etc.
        '''
        # Create Pipe connection
        parent_conn, child_conn = Pipe()
        self.listener_parent_conn = parent_conn
        self.listener_child_conn = child_conn

        # Create a Listener instance
        self.listener = Listener(data_type_list=data_type_list, 
                                 pipe=self.listener_child_conn)

        print "Listener initialised"


    def start_listener(self):
        '''Start Listener instance into a new daemonized thread.
        '''
        self.listener_thread = Thread(target=self.listener.run)
        self.listener_thread.setDaemon(True)
        self.listener_thread.start()
        print "Listener started"


    def restart_listener(self, address_list, msg_type_list):
        '''Restart listener after configuration update.
        '''
        self.listener.stop()
        self.init_listener(address_list, msg_type_list)
        self.start_listener()


    def cleanup(self):
        '''Cleanup Trollduction before shutdown.
        '''
        # TODO: add cleanup, close threads, and stuff
        pass


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

        while True:
            # wait for new messages
            msg = self.listener_parent_conn.recv()
            print msg
            # shutdown trollduction
            if msg.subject == '/StopTrollduction':
                self.cleanup()
                break
                #self.shutdown()
            # update trollduction config
            elif msg.subject == '/NewTrollductionConfig':
                self.update_td_config(msg.data)
            # update product lists
            elif msg.subject == '/NewProductConfig':
                self.update_product_config(msg.data)
            # process new file
            elif '/NewFileArrived' in msg.subject:
                self.time_slot = dt.datetime(msg.data['year'],
                                             msg.data['month'], 
                                             msg.data['day'],
                                             msg.data['hour'],
                                             msg.data['minute'])

                # orbit is empty string for meteosat, change it to None
                if msg.data['orbit'] == '':
                    msg.data['orbit'] = None

                t1a = time.time()

                self.global_data = GF.create_scene(\
                    satname=str(msg.data['satellite']), 
                    satnumber=str(msg.data['satnumber']), 
                    instrument=str(msg.data['instrument']), 
                    time_slot=self.time_slot, 
                    orbit=str(msg.data['orbit']))


                # Find maximum extent that is needed for all the
                # products to be made.
                self.get_maximum_extent()

                # Make images for each area
                for area_name in self.area_def_names:

                    t1b = time.time()

                    # Check which channels are needed. Unload
                    # unnecessary channels and load those that are not
                    # already available.
                    self.load_unload_channels(self.product_list[area_name])
                    # TODO: or something

                    # reproject to local domain
                    self.local_data = self.global_data.project(\
                        area_name, mode='nearest')
                    
                    print "Data reprojected for area:", area_name

                    # Draw requested images for this area.
                    self.draw_images(area_name)
                    print "Single area time elapsed time:", time.time()-t1b, 's'

                self.local_data = None
                self.global_data = None
#                self.loaded_channels = []
                print "Full time elapsed time:", time.time()-t1a, 's'
            else:
                # Unhandled message types end up here
                # No need to log these?
                pass



    def get_maximum_extent(self):
        '''Get maximum extend needed to produce all defined areas.
        '''
        self.maximum_area_extent = [None, None, None, None]
        for area in self.area_def_names:
            extent = get_area_def(area)

            if self.maximum_area_extent[0] is None:
                self.maximum_area_extent = list(extent.area_extent)
            else:
                if self.maximum_area_extent[0] > extent.area_extent[0]:
                    self.maximum_area_extent[0] = extent.area_extent[0]
                if self.maximum_area_extent[1] > extent.area_extent[1]:
                    self.maximum_area_extent[1] = extent.area_extent[1]
                if self.maximum_area_extent[2] < extent.area_extent[2]:
                    self.maximum_area_extent[2] = extent.area_extent[2]
                if self.maximum_area_extent[3] < extent.area_extent[3]:
                    self.maximum_area_extent[3] = extent.area_extent[3]


    def load_unload_channels(self, product_list):
        '''Load channels that are required for the given list of
        products. Unload channels that are unnecessary.
        '''

        ch_names = []
        wavelengths = []
        for ch in self.global_data.channels:
            ch_names.append(ch.name)
            wavelengths.append(ch.wavelength_range)
            
#        loaded = self.global_data.loaded_channels()
#        for l in loaded:
#            print l.wavelength_range
        required = []
#        to_load = []
#        to_unload = []

        for product in product_list:
            req = eval('self.global_data.image.'+product+'.prerequisites')
            for r in req:
                # get channel name
                for i in range(len(wavelengths)):
                    if r >= wavelengths[i][0] and r <= wavelengths[i][-1]:
                        n = ch_names[i]
                        break
                if n not in required:
                    required.append(n)

        self.global_data.load(required, self.maximum_area_extent)

        # At this time we only load all the required channels with
        # maximum extent. The code below could be tuned to also unload
        # extra channels.
        
        '''
                if n not in to_load and n not in self.loaded_channels:
                    to_load.append(n)

        for c in self.loaded_channels:
            if c not in required:
                to_unload.append(c)
                self.loaded_channels.remove(c)

        if len(to_load) > 0:
            print "load channels:", to_load
            self.global_data.load(to_load)
            if len(self.loaded_channels) == 0:
                self.loaded_channels = to_load
        if len(to_unload) > 0:
            print "unload channels:", to_unload
            self.global_data.unload(to_unload)
        '''



    def draw_images(self, area_name):
        '''Generate images from local data using given area name and
        product definitions.
        '''

        # Create images for each color composite
        for product in self.product_list[area_name]:
            # Parse image filename
            fname = self.image_output_dir + '/' + self.image_filename_template
            fname = fname.replace('%Y', '%04d' % self.time_slot.year)
            fname = fname.replace('%m', '%02d' % self.time_slot.month)
            fname = fname.replace('%d', '%02d' % self.time_slot.day)
            fname = fname.replace('%H', '%02d' % self.time_slot.hour)
            fname = fname.replace('%M', '%02d' % self.time_slot.minute)
            fname = fname.replace('%(area)', area_name)
            fname = fname.replace('%(composite)', product)
            fname = fname.replace('%(ending)', 'png')

            try:
                # Check if this combination is defined
                func = getattr(self.local_data.image, product)
                img = func()            
                img.save(fname)
                print "Image", fname, "saved."

                # TODO: log succesful production
                # TODO: publish message
            except AttributeError:
                # TODO: log incorrect product name
                print "Incorrect product name:", product, "for area", area_name
            except KeyError:
                # TODO: log missing channel
                print "Missing channel on", product, "for area", area_name
            except:
                # TODO: log other errors
                print "Undefined error on", product, "for area", area_name

        # TODO: log completion of this area def
        # TODO: publish completion of this area def


def read_config_file(fname=None):
    '''Read config file to dictionary.
    '''
    
    # TODO: check validity
    # TODO: read config, parse to dict, logging
    
    if fname is None:
        return None
    else:
        # TODO: read config
        return None


