from multiprocessing import Pipe
from multiprocessing.pool import ThreadPool
from threading import Thread
from listener import Listener
#from publisher import Publisher
#from logger import Logger
from mpop.satellites import GenericFactory as GF
import datetime as dt
import time

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
            self.update_tdconfig()

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
            self.publisher = None
            self.logger = None
            self.image_output_dir = None
            self.production_type = None
            self.pool = None
            self.pool_size = None

    def update_tdconfig(self, fname=None):
        '''Read Trollduction master configuration file and update the
        class fields.
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
            self.init_listener(td_config['listener']['address_list'],
                               td_config['listener']['msg_type_list'])
            self.restart_listener()

        if 'num_processes' in keys:
            # TODO: check if changed
            self.init_pool(num_processes=td_config['num_processes'])
        else:
            self.init_pool()

        if '' in keys:
            # TODO: check if changed
            pass


    def update_product_config(self, fname=None):
        '''Read area definitions and associated product names from a
        file and update the values for self.
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


    def init_listener(self, address_list, msg_type_list):
        '''Initialise listener that receives messages about new files
        to be processed, etc.
        '''
        # Create Pipe connection
        parent_conn, child_conn = Pipe()
        self.listener_parent_conn = parent_conn
        self.listener_child_conn = child_conn

        print "Pipe()"

        # Create a Listener instance
        self.listener = Listener(address_list=address_list, 
                                 msg_type_list=msg_type_list, 
                                 pipe=self.listener_child_conn)
        #self.listener.add_address_list(address_list)
        #self.listener.type_list = msg_type_list

        # Create subscriber
        #self.listener.create_subscriber()
        print "Listener initialised"


    def start_listener(self):
        '''Start Listener instance into a new daemonized thread.
        '''
        self.listener_thread = Thread(target=self.listener.run)
        self.listener_thread.setDaemon(True)
        self.listener_thread.start()
        print "Listener started"


    def restart_listener(self):
        '''Restart listener
        '''
        self.listener.stop()
        self.init_listener()
        self.start_listener()


    def init_pool(self, num_processes=2):
        '''Initialise worker pool with num_processes workers.
        '''
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
        self.pool = ThreadPool(processes=num_processes)
        self.pool_size = num_processes
        print 'Pool initialised'


    def cleanup(self):
        '''Cleanup everything before shutdown
        '''
        # TODO: add cleanup, close threads, and stuff
        pass


    def shutdown(self):
        '''Shutdown trollduction
        '''
        self.cleanup()
        sys.exit()


    def run_single(self):
        '''Run image production without threading.
        '''

        # TODO: Get relevant preprocessing function for this
        # production chain types eg.: swath, geo, granule, global_polar,
        # global_geo, global_mixed
        # preproc_func = getattr(preprocessing, self.production_type)

        while True:
            # wait for new messages
            msg = self.listener_parent_conn.recv()
            print msg
            # shutdown trollduction
            if msg.subject == '/StopTrollduction':
                self.shutdown()
            # update trollduction config
            elif msg.subject == '/td_config':
                self.update_td_config(msg.data)
            # update product lists
            elif msg.subject == '/product_config':
                self.udpate_product_config(msg.data)
            # process new file
            elif msg.subject == '/NewFileArrived':
                time_slot = dt.datetime(msg.data['year'],
                                        msg.data['month'], 
                                        msg.data['day'],
                                        msg.data['hour'],
                                        msg.data['minute'])

                global_data = GF.create_scene(str(msg.data['satellite']), 
                                              str(msg.data['satnumber']), 
                                              str(msg.data['instrument']), 
                                              time_slot, 
                                              str(msg.data['orbit']))

                t1a = time.time()

                global_data.load()
#                global_data.load(['1','2','3B','4','5'])

                t1 = time.time()
                for area_name in self.area_def_names:
                    # TODO: assemble a list of required channels
                    # TODO: find maximum extent that is needed
                    # TODO: global_data.load(required_channels)
                    # TODO: unload channels not required
                    # TODO: or something

                    # reproject to local domain

                    local_data = global_data.project(area_name)
                    
                    print "Data reprojected for area:", area_name
#                    draw_images_thread(local_data, area_name, 
#                                       self.product_list[area_name])
                    draw_images(local_data, area_name, self.product_list[area_name])

                local_data = None
                global_data = None
                print "Elapsed time:", time.time()-t1, 's'
            else:
                # Unhandled message types end up here
                pass

    def run_threads(self):
        '''Run image production in threads (#threads = #areas)
        '''

        # Get relevant preprocessing function for this production chain
        # types: swath, geo, granule, global_polar, global_geo, global_mixed
        # preproc_func = getattr(preprocessing, self.production_type)

        while True:
            # wait for new messages
            msg = self.listener_parent_conn.recv()
            print msg
            # shutdown trollduction
            if msg.subject == 'stop':
                self.cleanup()
                sys.exit()
            # update trollduction config
            elif msg.subject == 'td_config':
                self.update_td_config(msg.data)
            # update product lists
            elif msg.subject == 'product_config':
                self.udpate_product_config(msg.data)
            # process new file
            elif msg.subject == '/NewFileArrived':
                # TODO: parse inputs
                time_slot = dt.datetime(msg.data['year'],
                                        msg.data['month'], 
                                        msg.data['day'],
                                        msg.data['hour'],
                                        msg.data['minute'])

                global_data = GF.create_scene(str(msg.data['satellite']), 
                                              str(msg.data['satnumber']), 
                                              str(msg.data['instrument']), 
                                              time_slot, 
                                              str(msg.data['orbit']))

                global_data.load() #[0.635, 0.85, 10.8])

                threads = []
                local_data = []

                t1 = time.time()
                for area_name in self.area_def_names:
                    # TODO: assemble required channels for this area
                    # TODO: global_data.load(required_channels)
                    # TODO: unload channels not required
                    # reproject to local domain
                    local_data.append(global_data.project(area_name))
                    
                    print "Data reprojected for area:", area_name

                    # Send local data for colorcomposit generation & saving
                    t = Thread(target=draw_images, args=(local_data[-1], 
                                                         area_name, 
                                                         self.product_list[area_name]))
                    t.setDaemon(True)
                    t.start()
                    threads.append(t)

                for t in threads:
                    t.join()

                local_data = []
                global_data = None
                print "Elapsed time:", time.time()-t1, 's'
            else:
                # Unhandled message types end up here
                pass

    def run_thread_pool(self):
        '''Run image production using a thread pool.
        '''

        # Get relevant preprocessing function for this production chain
        # types: swath, geo, granule, global_polar, global_geo, global_mixed
        # preproc_func = getattr(preprocessing, self.production_type)

        while True:
            # wait for new messages
            msg = self.listener_parent_conn.recv()
            print msg
            # shutdown trollduction
            if msg.subject == 'stop':
                self.cleanup()
                sys.exit()
            # update trollduction config
            elif msg.subject == 'td_config':
                self.update_td_config(msg.data)
            # update product lists
            elif msg.subject == 'product_config':
                self.udpate_product_config(msg.data)
            # process new file
            elif msg.subject == '/NewFileArrived':
                # TODO: parse inputs
                time_slot = dt.datetime(msg.data['year'],
                                        msg.data['month'], 
                                        msg.data['day'],
                                        msg.data['hour'],
                                        msg.data['minute'])

                global_data = GF.create_scene(str(msg.data['satellite']), 
                                              str(msg.data['satnumber']), 
                                              str(msg.data['instrument']), 
                                              time_slot, 
                                              str(msg.data['orbit']))

                global_data.load() #[0.635, 0.85, 10.8])

                local_data = []
                if self.pool is None:
                    init_pool(num_processes=self.pool_size)

                t1 = time.time()
                for area_name in self.area_def_names:
                    # TODO: assemble required channels for this area
                    # TODO: global_data.load(required_channels)
                    # TODO: unload channels not required
                    # reproject to local domain
                    local_data.append(global_data.project(area_name))
                    
                    print "Data reprojected for area:", area_name

                    # Send local data for colorcomposit generation & saving

                    self.pool.apply_async(draw_images, 
                                          args=(local_data[-1],
                                                area_name,
                                                self.product_list[area_name]))

                self.pool.close()
                self.pool.join()
                self.pool = None

                local_data = []
                global_data = None
                print "Elapsed time:", time.time()-t1, 's'
            else:
                # Unhandled message types end up here
                pass


def draw_images(local_data, area_name, product_list):
    '''Generate images from local data using given area name and
    product definitions.
    '''

    # Create images for each color composite
    for product in product_list:
        try:
            print product
            # Check if this combination is defined
            func = getattr(local_data.image, product)
            img = func()
            
            # TODO real output filename parsing
            fname_out = '/home/lahtinep/Software/pytroll/output/' + \
                area_name + '_' + product + '.png'
            print fname_out
            img.save(fname_out)

            # TODO: log succesful production
            # TODO: publish message
        except AttributeError:
            # TODO: log incorrect product name
            print "Incorrect product name:", product, "for area", area_name
        except KeyError:
            # TODO: log missing channel
            print "Missing channel on:", product, "for area", area_name

    # TODO: log completion of this area def
    # TODO: publish completion of this area def


def draw_images_thread(local_data, area_name, product_list):
    '''Generate images from local data using given area name and
    product definitions.
    '''

    threads = []

    # Create images for each color composite
    for product in product_list:
        try:
            print product
            # Check if this combination is defined
            func = getattr(local_data.image, product)
            img = func()
            
            # TODO real output filename parsing
            fname_out = '/home/lahtinep/Software/pytroll/output/' + \
                area_name + '_' + product + '.png'
            print fname_out

            t = Thread(target=draw_and_save, args=(func, fname_out))
            t.setDaemon(True)
            t.start()
            threads.append(t)

            # TODO: log succesful production
            # TODO: publish message
        except AttributeError:
            # TODO: log incorrect product name
            print "AttributeError"

    for t in threads:
        t.join()
    # TODO: log completion of this area def
    # TODO: publish completion of this area def


def draw_and_save(func, fname_out):
    '''
    '''
    img = func()
    img.save(fname_out)


'''
    # removed, everything relevant will be received via messages
    def file_info(self, fname):
        #Parse information from filename.
        
        file_info = {}
        
        if self.production_type == 'hrpt':
            parts = fname.split('/')[-1].split('.')[0].split('_')
            file_info['satname'] = parts[1][:4]
            file_info['satnumber'] = parts[1][4:]
            file_info['instrument'] = avhrr
            time_slot = dt.datetime(int(parts[2][:4]),
                                    int(parts[2][4:6]),
                                    int(parts[2][6:]),
                                    int(parts[3][:2]),
                                    int(parts[3][2:]))
            file_info['time_slot'] = time_slot
            file_info['orbit'] = parts[4]
        else:
            file_info['satname'] = None
            file_info['satnumber'] = None
            file_info['instrument'] = None
            file_info['time_slot'] = None
            file_info['orbit'] = None

        # TODO: parse info, or replace create_scene() with a function
        # that can read files directly by filename

        return file_info
'''
