#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c14526.ad.smhi.se>

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

"""Unit testing some general purpose helper functions
"""

import unittest
from trollduction.helper_functions import overlapping_timeinterval
from datetime import datetime, timedelta


class TestTimeUtilities(unittest.TestCase):

    def setUp(self):
        """Setting up the testing
        """
        pass

    def test_overlapping_timeintervals(self):
        """Test the overlapping_timeinterval function"""

        timelist = [(datetime(2015, 1, 9, 17, 10, 48),
                     datetime(2015, 1, 9, 17, 21, 42)),
                    ]
        dt_start = datetime(2015, 1, 9, 17, 9, 0)
        dt_end = datetime(2015, 1, 9, 17, 23, 0)

        retv = overlapping_timeinterval((dt_start, dt_end), timelist)
        self.assertTrue(retv is not False)

        timelist = [(datetime(2015, 1, 9, 17, 6, 0),
                     datetime(2015, 1, 9, 17, 21, 0)),
                    (datetime(2014, 1, 9, 17, 6, 0),
                     datetime(2014, 1, 9, 17, 21, 0)), ]
        retv = overlapping_timeinterval((dt_start, dt_end), timelist)
        self.assertTrue(retv is not False)

        timelist = [(datetime(2015, 1, 9, 17, 20, 0),
                     datetime(2015, 1, 9, 17, 25, 0)),
                    ]
        retv = overlapping_timeinterval((dt_start, dt_end), timelist)
        self.assertTrue(retv is not False)

        timelist = [(datetime(2015, 1, 9, 17, 23, 1),
                     datetime(2015, 1, 9, 17, 29, 59)),
                    (datetime(2015, 1, 9, 17, 6, 1),
                     datetime(2015, 1, 9, 17, 8, 59)),
                    ]
        retv = overlapping_timeinterval((dt_start, dt_end), timelist)
        self.assertTrue(retv is False)

    def tearDown(self):
        """Closing down
        """
        pass


def suite():
    """The suite for test_trollduction
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestTimeUtilities))

    return mysuite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
