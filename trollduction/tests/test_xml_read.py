#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Martin Raspaud

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

"""Test xml_read.py
"""

import unittest

xmlstuff = """<?xml version="1.0" encoding='utf-8'?>
<?xml-stylesheet type="text/xsl" href="prodlist2.xsl"?>

<!-- This config is used by Trollduction.-->

<product_config>
  <metadata>
    <platform>noaa</platform>
    <number>15</number>
  </metadata>

  <common>
    <output_dir>/tmp</output_dir>
  </common>

  <variables>
    <output_dir id="local_sir">/local_disk/data/sir</output_dir>
    <output_dir id="sir">/local_disk/data/out/sir</output_dir>
    <output_dir id="rgb">/local_disk/data/out/rgb</output_dir>
    <output_dir id="tmp">/tmp</output_dir>
  </variables>

  <product_list>
    <!-- dump to netcdf -->
    <!-- calibrated, satellite projection -->
    <dump>
      <file output_dir="sir" format="netcdf4">{time:%Y%m%d_%H%M}_{platform}{satnumber}.nc</file>
    </dump>
    <area id="eurol" name="Europe_large">
      <!-- Generate the product only if sun is above the horizon at the
           defined longitude/latitude -->
      <product id="overview" name="overview" sunzen_day_maximum="90" sunzen_lonlat="25, 60">
        <file>{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
      </product>

      <product id="natural" name="dnc" sunzen_day_maximum="90" sunzen_lonlat="25, 60">
        <file>{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
      </product>

      <product id="green_snow" name="green_snow" sunzen_day_maximum="90" sunzen_lonlat="25, 60">
        <file>{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
      </product>

      <product id="red_snow" name="red_snow" sunzen_day_maximum="90" sunzen_lonlat="25, 60">
        <file format="png">{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
      </product>

      <product id="cloudtop" name="cloudtop">
        <file format="png">{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
      </product>

      <!-- Generate only if the Sun is below the horizon -->
      <product id="night_overview" name="night_overview" sunzen_night_minimum="90" sunzen_lonlat="25, 60">
        <file format="png">{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
      </product>

      <product id="night_fog" name="night_fog" sunzen_night_minimum="90" sunzen_lonlat="25, 60">
        <file>{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
      </product>

    </area>
  </product_list>
</product_config>
"""

from trollduction.xml_read import ProductList
from StringIO import StringIO


class TestProductList(unittest.TestCase):

    # def test_vars(self):
    #     pconfig = ProductList(StringIO(xmlstuff))
    #     self.assertEquals(pconfig.vars,
    #                       {'output_dir': {'local_sir': '/local_disk/data/sir',
    #                                       'rgb': '/local_disk/data/out/rgb',
    #                                       'sir': '/local_disk/data/out/sir',
    #                                       'tmp': '/tmp'}})
    #     dump_item = pconfig.pl.findall('./dump/file')[0]
    #     self.assertEquals(dump_item.attrib["output_dir"],
    #                      '/local_disk/data/out/sir')
    pass


def suite():
    """The suite for test_xml_read
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestProductList))

    return mysuite
