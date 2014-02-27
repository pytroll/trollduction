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
from listener import Listener, ListenerContainer

def hrpt():
    td = trollduction.Trollduction()
    td.area_def_names = ['euro4', 'scan', 'scan2', 'scan1']
    td.image_output_dir = '/tmp'
    td.image_filename_template = '%Y%m%d_%H%M_%(area)_%(composite).%(ending)'
    td.product_list = {'euro4': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview'],
                       'scan': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview'],
                       'scan2': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview'],
                       'scan1': ['overview', 'ir108', 'cloudtop', 'vis06', 'night_fog', 'night_overview']}
    td.production_type = 'hrpt_noaa_l1b'
    td.listener = ListenerContainer(data_type_list=['HRPT_l1b'])
    td.run_single()

def msg():
    td = trollduction.Trollduction()
    td.image_output_dir = '/tmp'
    td.image_filename_template = '%Y%m%d_%H%M_%(area)_%(composite).%(ending)'
    td.area_def_names = ['euro4', 'scan2', 'eurol']
    td.product_list = {'euro4': ['airmass', 'ash', 'cloudtop', 'convection', 'convection_co2', 'dust', 'fog', 'green_snow', 'ir108', 'natural', 'night_fog', 'night_microphysics', 'night_overview', 'overview', 'red_snow', 'vis06', 'wv_high', 'wv_low'],
                       'scan2': ['airmass', 'ash', 'cloudtop', 'convection', 'convection_co2', 'dust', 'fog', 'green_snow', 'ir108', 'natural', 'night_fog', 'night_microphysics', 'night_overview', 'overview', 'red_snow', 'vis06', 'wv_high', 'wv_low'],
                       'met09globeFull': ['airmass', 'ash', 'cloudtop', 'convection', 'convection_co2', 'dust', 'fog', 'green_snow', 'ir108', 'natural', 'night_fog', 'night_microphysics', 'night_overview', 'overview', 'red_snow', 'vis06', 'wv_high', 'wv_low'],
                       'eurol': ['airmass', 'ash', 'cloudtop', 'convection', 'convection_co2', 'dust', 'fog', 'green_snow', 'ir108', 'natural', 'night_fog', 'night_microphysics', 'night_overview', 'overview', 'red_snow', 'vis06', 'wv_high', 'wv_low'],
                       'MSGHRVN': ['airmass', 'ash', 'cloudtop', 'convection', 'convection_co2', 'dust', 'fog', 'green_snow', 'ir108', 'natural', 'night_fog', 'night_microphysics', 'night_overview', 'overview', 'red_snow', 'vis06', 'wv_high', 'wv_low']}
    td.production_type = 'msg_xrit'
    td.listener = ListenerContainer(data_type_list=['HRIT_lvl1.5'])
    td.run_single()
    

if __name__ == '__main__':

#    hrpt()
    msg()
