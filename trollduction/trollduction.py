
from listener import Listener
from publisher import Publisher
from logger import Logger

import mpop.satellites.GenericFactory as GF

class Trollduction(object):
    '''Trollduction class for easy generation chain setup
    '''

    def __init__(self, td_config_file=None):
        '''Init Trollduction instance
        '''

        # configuration file for the Trollduction instance
        self.td_config_file = td_config_file

        # read everything from the Trollduction config file
        if config is not None:
            self.update_tdconfig()

        # otherwise set empty placeholders
        else:
            self.product_list_file = None
            self.area_def_names = None
            # product list is a dict with area def names as keys and
            # product names as value arrays
            # eg. {'euro4km': ['greensnow', 'overview']}
            self.product_list = None
            self.listener = None
            self.listener_thread = None
            self.listener_parent_conn = None
            self.listener_child_conn = None
            self.publisher = None
            self.logger = None
            self.image_output_dir = None


    def update_tdconfig(self, fname=None):
        '''Read Trollduction master configuration file and update the
        class fields.
        '''
        if fname is not None:
            self.td_config_file = fname
            td_config = read_config_file(fname)
        elif self.td_config_file is not None:
            td_config = read_config_file(self.td_config_file)
        else:
            return
            
        keys = td_config.keys()

        if 'listener' in keys:
            self.init_listener(td_config['listener']['address_list'],
                               td_config['listener']['msg_type_list'])
            self.start_listener()

        if 'num_processes' in keys:
            self.init_pool(num_processes=td_config['num_processes'])
        else:
            self.init_pool()

        if '' in keys:
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

        # add checks or do we just assume the config to be valid at
        # this point?
        self.product_config = product_config


    def read_config_file(self, fname=None):
        '''Read config file to dictionary.
        '''
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

        # Create a Listener instance
        self.listener = Listener(pipe=self.listener_child_conn)
        self.listener.add_address_list(address_list)
        self.listener.type_list = msg_type_list

        # Create subscriber
        self.listener.create_subscriber()


    def start_listener(self):
        '''Start Listener instance into a new daemonized thread.
        '''
        self.listener_thread = Thread(target=self.listener.start)
        self.listener_thread.setDaemon(True)
        self.listener_thread.start()


    def init_pool(num_processes=2):
        '''Initialise worker pool with num_processes workers.
        '''
        self.pool = Pool(processes=num_processes)


    def shutdown(self):
        '''Shutdown trollduction
        '''

        # TODO: add cleanup and stuff
        sys.exit()


    def start(self):
        '''Start image production.
        '''
        while True:
            # wait for new messages
            msg = self.listener_parent_conn.recv()

            # shutdown trollduction
            if msg.atype == 'stop':
                self.cleanup()
                sys.exit()
            # update trollduction config
            elif msg.atype == 'td_config':
                self.update_td_config(msg.data)
            # update product lists
            elif msg.atype == 'product_config':
                self.udpate_product_config(msg.data)
            # process new file
            elif msg.atype == 'file':
                # TODO: parse inputs
                file_info = get_file_info()
                # if self.type == 'polar':
                global_data = GF.create_scene(file_info['satname'], 
                                              file_info['satnumber'], 
                                              file_info['instrument'], 
                                              file_info['time_slot'], 
                                              file_info['orbit'])
                for area_name in self.area_def_names:
                    self.pool.apply_async(process, 
                                          args=(global_data,
                                                area_name,
                                                product_list[area_name]))
                del global_data
            else:
                # Unhandled message types end up here
                pass


    def file_info(self, fname):
        '''Parse information from filename.
        '''
        file_info = {}
        # placeholder values
        file_info['satname'] = None
        file_info['satnumber'] = None
        file_info['instrument'] = None
        file_info['time_slot'] = None
        file_info['orbit'] = None

        # TODO: parse info, or replace create_scene() with a function
        # that can read files directly by filename

        return file_info
        

    def process(self, global_data, area_name, product_list):
        '''Generate local images from global data using given area name and
        product definitions.
        '''
        # reproject to local domain
        local_data = global_data.project(area_name)
        # free memory by deleting local copy of global_data.
        global_data = None

        # Create images for each color composite
        for product in product_list:
            try:
                # Check if this combination is defined
                func = getattr(local_data, product)
                img = local_data.func()
                fname = '' # TODO filename parsing
                img.save(fname)
                # TODO: log succesful production
                # TODO: publish message
            except AttributeError:
                # TODO: log incorrect product name
                pass

        # TODO: log completion of this area def
        # TODO: publish completion of this area def
