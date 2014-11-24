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

import xml.etree.ElementTree as etree
import os
import logging

logger = logging.getLogger(__name__)


class InfoObject(object):

    def __init__(self, **attributes):
        self.info = attributes

    def __getattr__(self, name):
        try:
            return self.info[name]
        except KeyError:
            raise AttributeError

    def get(self, key, default=None):
        return self.info.get(key, default)


class Dataset(InfoObject):

    def __init__(self, data, **attributes):
        InfoObject.__init__(self, **attributes)
        self.data = data

    def __str__(self):
        return str(self.data) + "\n" + str(self.info)

    def __repr__(self):
        return repr(self.data) + "\n" + repr(self.info)

    def copy(self, copy_data=True):
        if copy_data:
            data = self.data.copy()
        else:
            data = self.data
        return Dataset(data, **self.info)


class ProductList(object):

    def __init__(self, fname):
        self.fname = fname

        tree = etree.parse(fname)
        self._xml = tree.getroot()
        self.pl = None
        self.attrib = {}
        self.vars = {}
        self.aliases = {}
        self.groups = []
        self.parse()

    def insert_vars(self):
        """Variable replacement
        """
        for item in self.pl.getiterator():
            for key in self.vars:
                if key in item.attrib and item.attrib[key] in self.vars[key]:
                    item.set(key, self.vars[key][item.attrib[key]])

    def check_groups(self):

        # create the "rest" group
        last_group = []
        for area in self.pl:
            assigned = False
            for group in self.groups:
                if area.attrib["id"] in group.data:
                    assigned = True
                    break
            if not assigned:
                last_group.append(area.attrib["id"])
        if last_group:
            self.groups.append(Dataset(last_group, id="_rest"))

        # replace area ids with actual xml area items
        groups = []
        for group in self.groups:
            new_group = Dataset([], **group.info)
            for area_id in group.data:
                assigned = False
                for area in self.pl:
                    if area.attrib["id"] == area_id:
                        new_group.data.append(area)
                        assigned = True
                        break
                if not assigned:
                    logger.warning("Couldn't find area %s in product list",
                                   area_id)
            groups.append(new_group)
        self.groups = groups

    def parse(self):
        for item in self._xml:
            if item.tag == "product_list":
                self.pl = item
            elif item.tag == "common":
                for citem in item:
                    self.attrib[citem.tag] = citem.text
            elif item.tag == "groups":
                for group in item:
                    self.groups.append(Dataset(group.text.split(","),
                                               **group.attrib))
            elif item.tag == "variables":
                if item.attrib:
                    res = [os.environ[env] != val
                           for env, val in item.attrib.items()]
                    if any(res):
                        continue
                for var in item:
                    self.vars.setdefault(
                        var.tag, {})[var.attrib["id"]] = var.text
            elif item.tag == "aliases":
                for alias in item:
                    self.aliases.setdefault(
                        alias.tag,
                        {})[alias.attrib["src"]] = alias.attrib['dst']
        self.insert_vars()
        self.check_groups()


def get_root(fname):
    '''Read XML file and return the root tree.
    '''

    tree = etree.parse(fname)
    root = tree.getroot()

    return root


def parse_xml(tree, also_empty=False):
    '''Parse the given XML file to dictionary.
    '''
    xml_dict = {}

    # this tags will always be lists, if they are present and non-empty
    listify = ['area', 'product', 'valid_satellite', 'invalid_satellite',
               'pattern', 'file_tag', 'directory']
    children = list(tree)

    if len(children) == 0:
        try:
            xml_dict = tree.text.strip()
        except AttributeError:
            pass

    for child in children:
        new_val = parse_xml(child, also_empty=also_empty)
        if len(new_val) == 0:
            if also_empty:
                xml_dict[child.tag] = ''
                continue
            else:
                continue
        if child.tag in xml_dict:
            if not isinstance(xml_dict[child.tag], list):
                xml_dict[child.tag] = [xml_dict[child.tag]]
            xml_dict[child.tag].append(new_val)
        else:
            if len(new_val) > 0:
                if child.tag in listify:
                    xml_dict[child.tag] = [new_val]
                else:
                    xml_dict[child.tag] = new_val

    return xml_dict


def get_filepattern_config(fname=None):
    '''Retrieves the filepattern configuration file for trollstalker,
    and returns the parsed XML as a dictionary.  Optional argument
    *fname* can be used to specify the file.  If *fname* is None, the
    systemwide file is read.
    '''

    if fname is None:
        fname = os.path.realpath(__file__).split(os.path.sep)[:-2]
        fname.append('etc')
        fname.append('filepattern_config.xml')
        fname = os.path.sep.join(fname)

    return parse_xml(get_root(fname), also_empty=True)
