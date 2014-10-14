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

"""Test trollduction.py
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
    <path id="local_sir">/local_disk/data/sir</path>
    <path id="sir">/local_disk/data/out/sir</path>
    <path id="rgb">/local_disk/data/out/rgb</path>
    <path id="tmp">/tmp</path>
  </variables>

  <product_list>
    <!-- dump to netcdf -->
    <!-- calibrated, satellite projection -->
    <dump>
      <file format="netcdf4">{time:%Y%m%d_%H%M}_{platform}{satnumber}.nc</file>
    </dump>
    <area id="eurol" name="Europe_large">
      <!-- Generate the product only if sun is above the horizon at the
           defined longitude/latitude -->
      <product id="overview" name="overview" sunzen_day_maximum="90" sunzen_lonlat="25, 60">
        <file output_dir="tmp">{time:%Y%m%d_%H%M}_{platform}{satnumber}_{areaname}_{composite}.png</file>
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

msg = 'pytroll://AAPP-HRPT/1b/norrköping/utv/polar/direct_readout/ file safusr.u@lxserv248.smhi.se 2014-10-08T11:06:36.185553 v1.01 application/json {"satellite": "NOAA 19", "format": "AAPP-HRPT", "start_time": "2014-10-08T10:50:37.848000", "level": "1b", "orbit_number": "29197", "uri": "ssh://c20035.ad.smhi.se//local_disk/data/satellite/polar/noaa19_20100224_1129_05402/hrpt_noaa19_20100224_1129_05402.l1b", "filename": "hrpt_noaa19_20100224_1129_05402.l1", "instrument": "avhrr", "end_time": "2014-10-08T11:04:37.848000", "type": "Binary"}'


from StringIO import StringIO

from posttroll.message import Message
from mock import MagicMock, patch
import time
from datetime import datetime


class TestDataProcessor(unittest.TestCase):

    @patch('mpop.satellites.GenericFactory')
    def test_run(self, GF):
        from trollduction.producer import DataProcessor
        from trollduction.xml_read import ProductList
        pconfig = ProductList(StringIO(xmlstuff))
        dproc = DataProcessor()
        dproc.writer.stop()
        time.sleep(1)
        dproc.writer = MagicMock()
        dproc.draw_images = MagicMock()
        dproc.run(pconfig,  Message(rawstr=msg))
        GF.create_scene.assert_called_once_with(instrument='avhrr',
                                                satname='noaa',
                                                time_slot=datetime(
                                                    2014, 10, 8, 10, 50, 37, 848000),
                                                orbit='29197',
                                                satnumber='19')


def suite():
    """The suite for test_image
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestDataProcessor))

    return mysuite
