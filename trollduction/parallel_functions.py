
    def init_pool(self, num_processes=2):
        '''Initialise worker pool with num_processes workers.
        '''
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
        self.pool = ThreadPool(processes=num_processes)
        self.pool_size = num_processes
        print 'Pool initialised'



    def run_thread(self):
        '''Run image drawing in one thread
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
            elif '/NewFileArrived' in msg.subject:
                time_slot = dt.datetime(msg.data['year'],
                                        msg.data['month'], 
                                        msg.data['day'],
                                        msg.data['hour'],
                                        msg.data['minute'])

                if msg.data['orbit'] == '': msg.data['orbit'] = None

                t1a = time.time()

                self.global_data = GF.create_scene(satname=str(msg.data['satellite']), 
                                                   satnumber=str(msg.data['satnumber']), 
                                                   instrument=str(msg.data['instrument']), 
                                                   time_slot=time_slot, 
                                                   orbit=str(msg.data['orbit']))

#                print self.global_data.channels[0].wavelength_range



#                global_data.load(['VIS006', 'VIS008', 'IR_016', 'IR_039', 'WV_062', 'WV_073', 'IR_087', 'IR_097', 'IR_108', 'IR_120', 'IR_134']) #[0.635, 0.85, 10.8])

                thread = None
#                local_data1 = None
#                local_data2 = None

                i = 0
                for area_name in self.area_def_names:

                    t1b = time.time()

                    # TODO: assemble required channels for this area
                    # TODO: global_data.load(required_channels)
                    # TODO: unload channels not required
                    self.current_area_extent = get_area_def(area_name)
                    self.load_unload_channels(self.product_list[area_name])

                    # reproject to local domain
                    if i%2 == 0:
                        print "Starting reprojecting", i, "data1"
                        local_data1 = self.global_data.project(area_name, mode='nearest')
                    else:
                        print "Starting reprojecting", i, "data2"
                        local_data2 = self.global_data.project(area_name, mode='nearest')
                    
#                    if area_name == self.area_def_names[-1]:
#                        self.global_data = None

                    print "Data reprojected for area:", area_name

                    if thread is not None:
                        print "joining"
                        thread.join()
                        print "joined"

                    # Send local data for color composite generation & saving
                    if i%2 == 0:
                        thread = Thread(target=draw_images, 
                                        args=(local_data1, 
                                              area_name, 
                                              self.product_list[area_name]))
#                        print "local1"
#                        local_data2 = None
                    else:
                        thread = Thread(target=draw_images, 
                                        args=(local_data2, 
                                              area_name, 
                                              self.product_list[area_name]))
 #                       print "local2"
 #                       local_data1 = None
                    thread.setDaemon(True)
                    thread.start()
                    i += 1
                    
                    print "Single area time elapsed time:", time.time()-t1b, 's'

                if thread is not None:
                    while thread.isAlive():
                        thread.join()

                local_data1 = None
                local_data2 = None
                self.global_data = None
                self.loaded_channels = []
                print "Full time elapsed time:", time.time()-t1a, 's'
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
            elif '/NewFileArrived' in msg.subject:
                # TODO: parse inputs
                time_slot = dt.datetime(msg.data['year'],
                                        msg.data['month'], 
                                        msg.data['day'],
                                        msg.data['hour'],
                                        msg.data['minute'])

                self.global_data = GF.create_scene(str(msg.data['satellite']), 
                                                   str(msg.data['satnumber']), 
                                                   str(msg.data['instrument']), 
                                                   time_slot, 
                                                   str(msg.data['orbit']))

                channel_list = ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'WV_062', 'WV_073', 'IR_087', 'IR_097', 'IR_108', 'IR_120', 'IR_134']
                self.global_data.load(channel_list) #[0.635, 0.85, 10.8])

                threads = []
                local_data = []

                t1 = time.time()
                for area_name in self.area_def_names:
                    # TODO: assemble required channels for this area
                    # TODO: global_data.load(required_channels)
                    # TODO: unload channels not required
                    # reproject to local domain
                    local_data.append(self.global_data.project(area_name, mode='nearest'))
                    
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
                self.global_data = None
                self.loaded_channels = []
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
            elif '/NewFileArrived' in msg.subject:
                # TODO: parse inputs
                time_slot = dt.datetime(msg.data['year'],
                                        msg.data['month'], 
                                        msg.data['day'],
                                        msg.data['hour'],
                                        msg.data['minute'])

                self.global_data = GF.create_scene(str(msg.data['satellite']), 
                                                   str(msg.data['satnumber']), 
                                                   str(msg.data['instrument']), 
                                                   time_slot, 
                                                   str(msg.data['orbit']))

                channel_list = ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'WV_062', 'WV_073', 'IR_087', 'IR_097', 'IR_108', 'IR_120', 'IR_134']
                self.global_data.load(channel_list) #[0.635, 0.85, 10.8])

                local_data = []
                if self.pool is None:
                    init_pool(num_processes=self.pool_size)

                t1 = time.time()
                for area_name in self.area_def_names:
                    # TODO: assemble required channels for this area
                    # TODO: global_data.load(required_channels)
                    # TODO: unload channels not required
                    # reproject to local domain
                    local_data.append(global_data.project(area_name, mode='nearest'))
                    
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
                self.global_data = None
                self.loaded_channels = []
                print "Elapsed time:", time.time()-t1, 's'
            else:
                # Unhandled message types end up here
                pass

def draw_images_thread(local_data, area_name, product_list):
    '''Generate images from local data using given area name and
    product definitions.
    '''

    threads = []
    t1 = None
    t2 = None
    t3 = None
    t4 = None

    # Create images for each color composite
    for product in product_list:
        try:
            print product
            # Check if this combination is defined
            func = getattr(local_data.image, product)
            img = func()
            
            # TODO real output filename parsing
            fname_out = '/home/lahtinep/Software/pytroll/output/' + \
                area_name + '_' + product + '_msg.png'
            print fname_out

#            t = Thread(target=draw_and_save, args=(func, fname_out))
#            t.setDaemon(True)
#            t.start()
#            threads.append(t)
#            pool.apply_async(draw_and_save, args=(func, fname_out))
            t1 = Thread(target=draw_and_save, args=(func, fname_out))
            t1.setDaemon(True)
            t1.start()
            t2 = Thread(target=draw_and_save, args=(func, fname_out))
            t2.setDaemon(True)
            t2.start()
            t3 = Thread(target=draw_and_save, args=(func, fname_out))
            t3.setDaemon(True)
            t3.start()
            t4 = Thread(target=draw_and_save, args=(func, fname_out))
            t4.setDaemon(True)
            t4.start()

            t1.join()
            t2.join()
            t3.join()
            t4.join()

            # TODO: log succesful production
            # TODO: publish message
        except AttributeError:
            # TODO: log incorrect product name
            print "AttributeError"
        except:
            # TODO: log other errors
            print "General error on:", product, "for area", area_name

#    for t in threads:
#        t.join()
#    pool.close()
#    pool.join()
    # TODO: log completion of this area def
    # TODO: publish completion of this area def


def draw_and_save(func, fname_out):
    '''
    '''
    img = func()
    img.save(fname_out)
