#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c20671.ad.smhi.se>

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

"""Read the pps config file, and check validity of the entries during loading

"""

from ConfigParser import SafeConfigParser

supported_stations = ['kumpula', 'helsinki', 'norrkoping', 'nkp']


def read_config_file_options(filename, station, env, valid_config=None):
    """
    Read and checks config file
    If ok, return configuration dictionary
    """
    config = SafeConfigParser()

    if valid_config == None:
        valid_config = VALID_CONFIGURATION

    # Config variable will be replaced by following config
    optional_config_variables = valid_config['optional_config']
    mandatory_config_variables = valid_config['valid_config_variables']

    configuration = {}
    configuration['station'] = station
    configuration['environment'] = env
    config.read(filename)
    try:
        config_opts = dict(config.items(env, raw=False))
    except Exception as err:
        print " Section %s %s" % (env,
                                  "is not defined in your" +
                                  "aapp_runner config file!")
        return None
    # Read config file
    for item in mandatory_config_variables:
        try:
            configuration[item] = config_opts[item]
#            print "Required variable: ", item
            if item in optional_config_variables and config_opts[item] == '':
                #                print "This will be replaced:", item
                new_item = optional_config_variables.get(item, item)
                print (item, "was not defined. Value from",
                       new_item, "will be used.")
                configuration[item] = config_opts[new_item]
        except KeyError as err:
         #           print "---------"
         #           if item in optional_config_variables:
         #               #print "This will be replaced:", item
         #               new_item = optional_config_variables.get(item, item)
         #               print (item, "was not defined. Value from",
         #                      new_item, "will be used.")
         #               configuration[item] = config_opts[new_item]
         #           else:
            print "%s %s %s" % (err.args,
                                "is missing."
                                "Please, check your config file",
                                filename)
            return None

    # Fix the list of subscribe topics:
    topics = configuration['subscribe_topics'].split(',')
    topiclist = []
    for topic in topics:
        topiclist.append(topic.strip(' '))
    configuration['subscribe_topics'] = topiclist

    # print "DATASERVER is", configuration['dataserver']
    if not check_config_file_options(configuration, valid_config):
        return None

    return configuration
