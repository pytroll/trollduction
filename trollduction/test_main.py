#!/usr/bin/python

from multiprocessing import Pool, Pipe
from threading import Thread
#from listener import Listener
#from publisher import Publisher
#from logger import Logger
from mpop.satellites import GenericFactory as GF
import trollduction
import sys
from posttroll.publisher import get_own_ip

if __name__ == '__main__':

    #fname = sys.argv[1]

    td = trollduction.Trollduction()
    td.area_def_names = ['euro4', 'scan', 'scan2', 'scan1']
    td.product_list = {'euro4': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview'],
                       'scan': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview'],
                       'scan2': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview'],
                       'scan1': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview']}
    td.image_output_dir = '/home/lahtinep/Software/pytroll/output'
    td.production_type = 'hrpt'
#    td.init_pool(num_processes=4)
    td.init_listener(['tcp://'+get_own_ip()+':9000'], ['hrpt_noaa'])
    td.start_listener()
    td.run_single()
#    td.run_threads()
#    td.run_thread_pool()
    
