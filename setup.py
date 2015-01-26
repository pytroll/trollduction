#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014, 2015 Martin Raspaud

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

"""Setup for trollduction.
"""
from setuptools import setup
import imp

version = imp.load_source('trollduction.version', 'trollduction/version.py')

setup(name="trollduction",
      version=version.__version__,
      description='Pytroll batch production library',
      author='Martin Raspaud',
      author_email='martin.raspaud@smhi.se',
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 " +
                   "or later (GPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering"],
      url="https://github.com/mraspaud/trollduction",
      packages=['trollduction', 'npp_runner',
                'modis_runner', 'trollduction.collectors'],
      scripts=['bin/trollstalker.py',
               'bin/gatherer.py',
               'npp_runner/viirs_dr_runner.py',
               'modis_runner/modis_dr_runner.py',
               'bin/aapp_runner.py',
               'bin/pps_runner.py',
               'bin/l2processor.py',
               'bin/scisys_receiver.py'],
      data_files=[],
      zip_safe=False,
      install_requires=['pyinotify', 'mpop', 'posttroll',
                        'pyresample', 'pykdtree',
                        'trollimage', 'pyorbital',
                        'trollsift', 'netifaces',
                        'pytroll-schedule', 'netcdf4'],
      test_requires=['mock'],
      test_suite='trollduction.tests.suite',
      )
