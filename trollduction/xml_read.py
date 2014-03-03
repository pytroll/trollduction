#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014

# Author(s):

#   Panu Lahtinen <pnuu+git@iki.fi>

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

'''XML reader for Trollduction system and product configuration files.
'''

from lxml import etree

def get_root(fname):
    '''Read XML file and return the root tree.
    '''

    tree = etree.parse(fname)
    root = tree.getroot()

    return root


def parse_xml(tree):
    '''Parse the given XML file to dictionary.
    '''
    xml_dict = {}

    # this tags will always be lists, if they are present and non-empty
    listify = ['area', 'product', 'valid_satellite', 'invalid_satellite']
    children = list(tree)

    
    if len(children) == 0:
        try:
            xml_dict = tree.text.strip()
        except AttributeError:
            pass

    for child in children:
        if not isinstance(child, etree._Comment):
            new_val = parse_xml(child)
            if len(new_val) == 0:
                continue
            if xml_dict.has_key(child.tag):
                if not type(xml_dict[child.tag]) == list:
                    xml_dict[child.tag] = [xml_dict[child.tag]]
                xml_dict[child.tag].append(new_val)
            else:
                if len(new_val) > 0:
                    if child.tag in listify:
                        xml_dict[child.tag] = [new_val]
                    else:
                        xml_dict[child.tag] = new_val

    return xml_dict
