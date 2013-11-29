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

"""
Read the xml product lists and generate batch jobs.

Scenarios:

SMHI setup:
a batch executable to use as a daemon (usually) -> run_on_list

Future (?):
Send a batch of requests -> batch_generator & caller daemon

NB: don't forget hooks to send messages in the end.
"""

import os.path

import xml.etree.ElementTree as ET

def read_product_file(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    product_list = {}

    variables = {}

    for variable in root.find("variables"):
        variables.setdefault(variable.tag, {})
        variables[variable.tag][variable.attrib["id"]] = variable.text

    print variables

    for area in root.getiterator("area"):
        area_name = area.get("id")
        product_list[area_name] = {}
        for prod in area:
            prod_name =  prod.get("id")
            product_list[area_name][prod_name] = []
            for filename in prod:
                args = {}
                for attr in filename.attrib:
                    if attr == "path":
                        filepath = os.path.join(variables["path"][filename.get("path")],
                                                filename.text)
                    else:
                        try:
                            args[attr] = eval(filename.attrib[attr])
                        except NameError:
                            args[attr] = filename.attrib[attr]

                product_list[area_name][prod_name].append((filepath, args))

    return product_list, dict(root.find("metadata").attrib)

#import pprint
#pprint.pprint(read_product_file('/local_disk/usr/src/mpop-smhi.old/etc/noaa15_products.xml'))


def batch_generator(platform, variant, number, time_interval):
    filename = find_product_file(platform, variant, number)
    product_list, metadata = read_product_file(filename)
    # create request message(s?)


def handle_request(req):
    # create global_data for the satellite and datetime.


    # create requests from req
    for area in requests:
        l = g.project(area)
        for prod in requests[area]:
            img = getattr(prod, l.image)()
            # options + overlay and save
            
            img.save(requests[area][prod], **options)

            


def caller(satscene, composite, hooks):
    img = composite(satscene)
    return img

def post_proc(hooks):
    for hook in hooks:
        hook(satscene)
