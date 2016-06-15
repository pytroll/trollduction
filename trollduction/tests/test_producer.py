#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015 Martin Raspaud

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

"""Tests for the producer.py module
"""


from trollduction.producer import coverage, get_polygons_positions
from trollduction.producer import check_uri
import numpy as np
import unittest
from mock import MagicMock
from pyresample.geometry import AreaDefinition


class TestPolygonCoverage(unittest.TestCase):

    def test_get_polygons_positions(self):
        data = np.arange(25).reshape(5, 5)
        mask = np.zeros((5, 5), dtype=np.bool)
        mask[2, :] = True
        data = np.ma.array(data, mask=mask)

        self.assertEquals(get_polygons_positions((data, )),
                          [[(1, 3), (1, 2), (1, 1), (1, 0),
                            (0, 0), (0, 4), (1, 4)],
                           [(4, 0), (3, 0), (3, 1), (3, 2),
                            (3, 3), (3, 4), (4, 4)]])

        data = np.arange(2500).reshape(50, 50)
        mask = np.zeros((50, 50), dtype=np.bool)
        mask[20:30, :] = True
        mask[40:, :] = True
        data = np.ma.array(data, mask=mask)

        self.assertEquals(get_polygons_positions((data, ), frequency=25),
                          [[(19, 26), (19, 1), (19, 0),
                            (0, 0), (0, 49), (19, 49)],
                           [(39, 0), (30, 0), (30, 1),
                            (30, 26), (39, 49)]])

        data = np.arange(2500).reshape(50, 50)
        mask = np.ones((50, 50), dtype=np.bool)
        data = np.ma.array(data, mask=mask)

        self.assertEquals(get_polygons_positions((data, ), frequency=25),
                          [])

    def test_coverage(self):

        chn = MagicMock()
        chn.is_loaded.return_value = True
        chn.shape = 3712, 3712
        chn.mask = np.zeros(chn.shape, dtype=bool)
        chn.mask[:1250, :] = True
        chn.mask[2500:, :] = True
        chn.mask[:, :1250] = True
        chn.mask[:, 2500:] = True
        chn.data = np.ma.array(np.ones(chn.shape), mask=chn.mask)
        chn.area = AreaDefinition("chn_area",
                                  "chn_area",
                                  "geos 0.0",
                                  {"proj": "geos",
                                   "lon_0": "0.0",
                                   "a": "6378169.00",
                                   "b": "6356583.80",
                                   "h": "35785831.0"},
                                  3712,
                                  3712,
                                  [-5567248.074173444, -5570248.4773392612,
                                   5570248.4773392612, 5567248.074173444])

        hrv = MagicMock()
        hrv.is_loaded.return_value = True
        hrv.shape = 11136, 11136
        hrv.mask = np.zeros(hrv.shape, dtype=bool)
        hrv.mask[:3500, :] = True
        hrv.mask[7700:, :] = True
        hrv.mask[:, :3500] = True
        hrv.mask[:, 7700:] = True
        hrv.data = np.ma.array(np.ones(hrv.shape), mask=hrv.mask)
        hrv.area = AreaDefinition("hrv_area",
                                  "hrv_area",
                                  "geos 0.0",
                                  {"proj": "geos",
                                   "lon_0": "0.0",
                                   "a": "6378169.00",
                                   "b": "6356583.80",
                                   "h": "35785831.0"},
                                  11136,
                                  11136,
                                  [-5570248.2560258955, -5567247.8529792884,
                                   5567247.8529792884, 5570248.2560258955])

        scene = MagicMock()

        scene.channels = (chn, hrv)

        mali = AreaDefinition("mali_area",
                              "mali_area",
                              "merc",
                              {"proj": "merc",
                               "ellps": "WGS84",
                               "lon_0": "-1.0",
                               "lat_0": "19.0"},
                              1024,
                              1024,
                              (-1224514.3987260093, 1111475.1028522244,
                               1224514.3987260093, 3228918.5790461157))

        self.assertEquals(0.44009280754700542, coverage(scene, mali))


class TestCheckUri(unittest.TestCase):

    def test_check_uri(self):

        URI1 = "ssh:///san1/pps/import/PPS_data/source/noaa19_20151016_0830_34458/amsual1b_noaa19_20151016_0830_34458.l1b"
        retv = check_uri(URI1)
        self.assertEqual(
            retv, "/san1/pps/import/PPS_data/source/noaa19_20151016_0830_34458/amsual1b_noaa19_20151016_0830_34458.l1b")
        URI2 = "ssh://mytestserver.myhost.xx/san1/pps/import/PPS_data/source/metop01_20151016_1007_15964/hrpt_metop01_20151016_1007_15964.l1b"
        retv = check_uri(URI2)
        self.assertEqual(
            retv, "/san1/pps/import/PPS_data/source/metop01_20151016_1007_15964/hrpt_metop01_20151016_1007_15964.l1b")


def suite():
    """The suite for test_xml_read
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestPolygonCoverage))
    mysuite.addTest(loader.loadTestsFromTestCase(TestCheckUri))

    return mysuite
