#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>

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


from posttroll.publisher import get_own_ip
from multiprocessing import Pipe
from mpop.utils import debug_on
debug_on()
from xml_read import read_product_file
from mpop.satellites import GenericFactory
from ConfigParser import ConfigParser


from threading import Thread, activeCount, Semaphore
import os
from listener import Listener
import logging

logger = logging.getLogger(__name__)

OWN_PORT = 9000
OWN_ADDRESS = str(get_own_ip())
#OWN_ADDRESS = str("127.0.0.1")

JOONAS_PORT = 9000
JOONAS_ADDRESS = "10.240.23.37"


def get_prerequisites(obj, product_list):
    """Get the required channels from scene *obj* according to *product_list*.
    """
    prereqs = set()
    for products in product_list.values():
        for prod in products:
            prereqs |= getattr(obj, prod).prerequisites
    return prereqs


MAIN_CONFIG_FILE = "./main.cfg"
MAIN_CONFIG = ConfigParser()
MAIN_CONFIG.read(MAIN_CONFIG_FILE)

class FileMissingError(Exception):
    """Exception when a file is missing.
    """
    pass


def get_productlist_filename(satellite, number, instrument, variant):
    proddir = MAIN_CONFIG.get("default", "productlist_dir")
    specific_file = os.path.join(proddir,
                                 variant + satellite + number + "_products.xml")
    generic_file = os.path.join(proddir,
                                instrument + "_products.xml")
    if os.path.exists(specific_file):
        return specific_file
    elif os.path.exists(generic_file):
        return generic_file
    else:
        raise FileMissingError(generic_file + " is missing !")
    

def generate_composites(global_data, area, prodlist, sem):
    """Generate the composites from *global_data* listed in *prodlist* for
    *area*.
    """
    print "Waiting for a free slot", area
    sem.acquire()
    print "Working hard!", area
    local_data = global_data.project(area)
    #local_data = global_data
    for prod, filenames in prodlist.items():
        img = getattr(local_data.image, prod)()
        for filename, options in filenames:
            sat_attrs = {"orbit": int(global_data.orbit)}
            new_filename = local_data.time_slot.strftime(filename)%sat_attrs
            logger.debug("saving " + new_filename)
            if "overlay" in options:
                img.add_overlay()
            img.save(new_filename, **options)

    sem.release()


    
def triage(msg, max_num_threads=1):
    """Determine what to do with *msg*.
    """
    info = msg.data

    filename = get_productlist_filename(info["satellite"],
                                        info["number"],
                                        info["instrument"],
                                        info.get("variant", ""))
    
    pl, mda = read_product_file(filename)
    logger.debug("Read product list: " + str(mda))
    global_data = GenericFactory.create_scene(str(info["satellite"]),
                                              str(info["number"]),
                                              str(info["instrument"]),
                                              info["start_time"],
                                              "%05d"%info["orbit_number"])
    
    channels = get_prerequisites(global_data.image, pl)
    
    global_data.load(channels)

    sem = Semaphore(max_num_threads)

    for area, products in pl.items():
        # FIXME: Number of simultaneous threads should be configurable
        # Fork bomb, fork bomb, I'm a fork bomb ! (Tom Jones)
        thr = Thread(target=generate_composites, args=(global_data,
                                                       area,
                                                       products,
                                                       sem))
        thr.start()
        logger.info("Started thread to process " + info["satellite"] +
                    info["number"] + " on " + area)


if __name__ == "__main__":

    parent_conn, child_conn = Pipe()

    listener = Listener(child_pipe=child_conn)
    print "subscribing to ", OWN_ADDRESS, OWN_PORT
    listener.add_address(OWN_ADDRESS, OWN_PORT)
    #print "subscribing to ", JOONAS_ADDRESS, JOONAS_PORT
    #listener.add_address(JOONAS_ADDRESS, JOONAS_PORT)
    #listener.type_list = ["type1", "NOAA19*.hmf"]
    listener.type_list = ["hmf"]
    #listener.type_list = []
    listener.create_subscriber()

    proc = Thread(target=listener.start)
    proc.setDaemon(True)
    proc.start()

    while True:
        msg = parent_conn.recv()
        #pool.apply_async(do_processing, args=(msg,))
        triage(msg)

        # Send reply that the message was received
        #publisher.send_ack(msg)
        #print msg
#        time.sleep(1)


