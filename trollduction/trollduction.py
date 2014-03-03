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

#from multiprocessing import Pipe
#from threading import Thread
from listener import ListenerContainer
#from publisher import Publisher
#from logger import Logger
from mpop.satellites import GenericFactory as GF
import datetime as dt
import time
from mpop.projector import get_area_def
import sys
import xml_read
from pprint import pprint

class Trollduction(object):
    '''Trollduction class for easy generation chain setup
    '''

    def __init__(self, td_config_file=None):
        '''Init Trollduction instance
        '''

        # configuration file for the Trollduction instance
        self.td_config_file = td_config_file
        self.td_config = None
        self.product_config = None
        self.listener = None
        self.satellite = {'satname': None,
                          'satnumber': None,
                          'instrument': None}
        self.global_data = None
        self.local_data = None

        # Not yet in use
        self.publisher = None
        self.logger = None
        

        # read everything from the Trollduction config file
        if self.td_config_file is not None:
            self.update_td_config()


    def update_td_config(self, fname=None):
        '''Update Trollduction configuration from the given file.
        '''

        if fname is not None:
            self.td_config_file = fname
            self.td_config = read_config_file(fname)
        elif self.td_config_file is not None:
            self.td_config = read_config_file(self.td_config_file)
        else:
            return
            
        print 'Trollduction configuration:'
        pprint(self.td_config)

        # Initialize/restart listener
        try:
            if self.listener is None:
                self.listener = ListenerContainer(\
                    data_type_list=self.td_config['listener_tag'])
            else:
                self.listener.restart_listener(self.td_config['listener_tag'])
        except KeyError:
            # TODO: logging
            print "Key 'listener_tag' is missing from " + self.td_config_file

        try:
            self.update_product_config(\
                fname=self.td_config['product_config_file'])
        except KeyError:
            print "Key 'product_config' is missing from " + self.td_config_file


    def update_product_config(self, fname=None):
        '''Update area definitions, associated product names, output
        filename prototypes and other relevant information from the
        given file.
        '''

        if self.td_config is None:
            self.td_config = {}
        if fname is not None:
            self.td_config['product_config_file'] = fname
            product_config = read_config_file(fname)
        elif self.td_config['product_config_file'] is not None:
            product_config = read_config_file(\
                self.td_config['product_config_file'])
        else:
            product_config = None

        # add checks, or do we just assume the config to be valid at
        # this point?
        self.product_config = product_config        

        print 'New product config:'
        pprint(self.product_config)


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
            msg = self.listener.parent_conn.recv()
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
                time_slot = dt.datetime(msg.data['year'],
                                        msg.data['month'], 
                                        msg.data['day'],
                                        msg.data['hour'],
                                        msg.data['minute'])
                self.satellite['satname'] = msg.data['satellite']
                self.satellite['satnumber'] = msg.data['satnumber']
                self.satellite['instrument'] = msg.data['instrument']

                # orbit is empty string for meteosat, change it to None
                if msg.data['orbit'] == '':
                    msg.data['orbit'] = None

                t1a = time.time()

                self.global_data = GF.create_scene(\
                    satname=str(self.satellite['satname']), 
                    satnumber=str(self.satellite['satnumber']), 
                    instrument=str(self.satellite['instrument']), 
                    time_slot=time_slot, 
                    orbit=str(msg.data['orbit']))


                # Find maximum extent that is needed for all the
                # products to be made.
#                maximum_area_extent = get_maximum_extent(self.area_def_names)
                
#                maximum_area_extent = get_maximum_extent(['EuropeCanary'])
                maximum_area_extent = None

                # Make images for each area
                for area in self.product_config['area']:

                    t1b = time.time()

                    # Check which channels are needed. Unload
                    # unnecessary channels and load those that are not
                    # already available.
                    self.load_unload_channels(area['product'], 
                                              max_extent=maximum_area_extent)
                    # TODO: or something

                    # reproject to local domain
                    self.local_data = self.global_data.project(\
                        area['definition'], mode='nearest')
                    
                    print "Data reprojected for area:", area['name']

                    # Draw requested images for this area.
                    self.draw_images(area)
                    print "Single area time elapsed time:", time.time()-t1b, 's'

                self.local_data = None
                self.global_data = None
#                self.loaded_channels = []
                print "Full time elapsed time:", time.time()-t1a, 's'
            else:
                # Unhandled message types end up here
                # No need to log these?
                pass



    def load_unload_channels(self, products, max_extent=None):
        '''Load channels that are required for the given list of
        products. Unload channels that are unnecessary.
        '''

        ch_names = []
        wavelengths = []
        for chan in self.global_data.channels:
            ch_names.append(chan.name)
            wavelengths.append(chan.wavelength_range)
            
#        loaded = self.global_data.loaded_channels()
#        for l in loaded:
#            print l.wavelength_range
        required = []
#        to_load = []
#        to_unload = []

        for product in products:
            reqs = eval('self.global_data.image.'+ \
                            product['composite']+'.prerequisites')
            for req in reqs:
                # get channel name
                for i in range(len(wavelengths)):
                    if req >= wavelengths[i][0] and req <= wavelengths[i][-1]:
                        name = ch_names[i]
                        break
                if name not in required:
                    required.append(name)

        self.global_data.load(required, max_extent)

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


    def draw_images(self, area):
        '''Generate images from local data using given area name and
        product definitions.
        '''

        pprint(area)

        # Create images for each color composite
        for product in area['product']:
            # Parse image filename
            fname = self.parse_filename(area, product)

            try:
                # Check if this combination is defined
                func = getattr(self.local_data.image, product['composite'])
                img = func()            
                img.save(fname)
                print "Image", fname, "saved."

                # TODO: log succesful production
                # TODO: publish message
            except AttributeError:
                # TODO: log incorrect product name
                print "Incorrect product name:", product['name'], \
                    "for area", area['name']
            except KeyError:
                # TODO: log missing channel
                print "Missing channel on", product['name'], \
                    "for area", area['name']
            except:
                err = sys.exc_info()[0]
                # TODO: log other errors
                print "Error", err, "on", product['name'], \
                    "for area", area['name']

        # TODO: log completion of this area def
        # TODO: publish completion of this area def


    def parse_filename(self, area, product):
        '''Parse filename for this product
        '''
        try:
            fname = product['output_dir']
        except KeyError:
            try:
                fname = area['output_dir']
            except KeyError:
                fname = self.product_config['common']['output_dir']
            
        fname += '/' + product['filename']
        fname = fname.replace('%Y', '%04d' % \
                                  self.local_data.time_slot.year)
        fname = fname.replace('%m', '%02d' % \
                                  self.local_data.time_slot.month)
        fname = fname.replace('%d', '%02d' % \
                                  self.local_data.time_slot.day)
        fname = fname.replace('%H', '%02d' % \
                                  self.local_data.time_slot.hour)
        fname = fname.replace('%M', '%02d' % \
                                  self.local_data.time_slot.minute)
        fname = fname.replace('%(areaname)', area['name'])
        fname = fname.replace('%(composite)', product['name'])
        fname = fname.replace('%(satellite)', 
                              self.satellite['satname'] + \
                                  self.satellite['satnumber'])
        fname = fname.replace('%(instrument)', 
                              self.satellite['instrument'])
        fname = fname.replace('%(ending)', 'png')
        
        return fname

                              
def read_config_file(fname=None):
    '''Read config file to dictionary.
    '''
    
    # TODO: check validity
    # TODO: logging
    
    if fname is None:
        return None
    else:
        return xml_read.parse_xml(xml_read.get_root(fname))


def get_maximum_extent(area_def_names):
    '''Get maximum extend needed to produce all defined areas.
    '''
    maximum_area_extent = [None, None, None, None]
    for area in area_def_names:
        extent = get_area_def(area)
        
        if maximum_area_extent[0] is None:
            maximum_area_extent = list(extent.area_extent)
        else:
            if maximum_area_extent[0] > extent.area_extent[0]:
                maximum_area_extent[0] = extent.area_extent[0]
            if maximum_area_extent[1] > extent.area_extent[1]:
                maximum_area_extent[1] = extent.area_extent[1]
            if maximum_area_extent[2] < extent.area_extent[2]:
                maximum_area_extent[2] = extent.area_extent[2]
            if maximum_area_extent[3] < extent.area_extent[3]:
                maximum_area_extent[3] = extent.area_extent[3]

    return maximum_area_extent

