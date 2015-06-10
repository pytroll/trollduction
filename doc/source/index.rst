.. trollduction documentation master file, created by
   sphinx-quickstart on Mon Feb 17 08:35:12 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to trollduction's documentation!
========================================

Trollduction is a configurable framework for satellite image batch production.

This documentation is a work in progress, but the most important bits should be present. The missing details will be added once noticed.

.. contents::
   :depth: 3

How does Trollduction work?
===========================

Trollduction builds on the principle that satellite image batch production is
event based, and that different processing steps are chained together to produce
the final products. This is why trollduction is a collection of independent
elements of this chain, which are then communicating together through
lightweight network messages.

The different elements provided are:
 - trollstalker: triggers an event message each time a file is put in given
   directory
 - l2processor: generates rgb/channel images when an appropriate event message is 
   received
 - gatherer: gathers polar satellite granules together given an area of
   interest, and sends an event message when a matching group of granules has
   been gathered
 - aapp_runner: runs the AAPP software on raw hrpt files, when such an event
   message is received, to generate level 1 data
 - viirs_dr_runner: runs the CSPP software on Suomi-NPP RDR files to generate
   level 1 data
 - modis_dr_runner: runs the SPA software on EOS-Terra/Aqua PDS files to
   generate level 1 data
 - pps_runner: triggers processing of PPS main script once AAPP or CSPP
   is ready with a level-1 file


Setting things up cheat sheet
=============================

1. Install other required packages:
    * libnetcdf-dev
    * libhdf5-dev
    * python-numpy
    * python-zmq
    * python-pyinotify

   and the Pytroll packages:

    * mpop_ - select *pre-master* branch
    * mipp_ - select *pre-master* branch
    * pyresample_ - select *pre-master* branch 
    * posttroll_ - select *develop* branch
    * pyorbital_ - select *develop* branch
    * trollsift_ - select *master* branch
    * trollduction_ - select *master* branch
    * pytroll-schedule_ - select *develop* branch
    * pyspectral_ - select *pre-master* branch
    * pykdtree_ - select *master* branch
    * python-geotiepoints_ - select *develop* branch
    * trollimage_ - select *develop* branch
    * pycoast_ - select *pre-master* branch 

#. Configure mpop
    * modify *mpop.cfg* to suit your needs
    * add configurations for satellites you are going to use (see the templates
      in `mpop/etc/`)
#. Create Trollduction configuration files
    * use *examples/trollstalker_config.ini_template* as a template
    * use *examples/l2processor_config.ini_template* as a template
    * save config file to your chosen place without the *_template* ending
#. Create Trollduction product configuration file
    * use *examples/product_config_hrpt.xml_template* as a template
    * save the file to the path defined in your *l2processor_config.ini*
      without the *_template* ending
    * define your output_dir in the xml file
    * topic from the *trollstalker_config.ini* must be included in the list
      of topics in *l2processor_config.ini*
#. Create logging configurations for *trollduction* and *trollstalker*
    * use *examples/l2processor_logging.ini_template* and
      *examples/trollstalker_logging.ini_template* as templates
    * check the log filename (by default logs go to */tmp/* directory)
    * save these configs to the path defined in your *l2processor_config.ini*
      and *trollstalker_config.ini* without the *_template* ending
#. Start *posttroll/bin/nameserver*
    * this will register the different subscribers on the network and relay the
      messages between different processes
    * *./nameserver*
#. Start *trollduction/bin/trollstalker.py*
    * file watcher that sends messages of new files available for processing
    * for example: *./trollstalker.py -c /path/to/trollstalker_config.ini
      -C noaa_hrpt*
#. Start Trollduction *trollduction/bin/l2processor.py*
    * *./l2processor.py -c /path/to/l2processor_config.ini -C noaa_hrpt*
    * this should print your configuration and stop to wait for new
      messages
#. Copy a suitable file to your data input directory
#. Check the output directory for images

.. _mpop: https://github.com/mraspaud/mpop
.. _mipp: https://github.com/loerum/mipp
.. _pyresample: https://github.com/mraspaud/pyresample
.. _posttroll: https://github.com/mraspaud/posttroll
.. _pyorbital: https://github.com/mraspaud/pyorbital
.. _trollsift: https://github.com/pnuu/trollsift
.. _trollduction: https://github.com/mraspaud/trollduction
.. _pytroll-schedule: https://github.com/mraspaud/pytroll-schedule
.. _pyspectral: https://github.com/adybbroe/pyspectral
.. _pykdtree: https://github.com/storpipfugl/pykdtree
.. _python-geotiepoints: https://github.com/adybbroe/python-geotiepoints
.. _trollimage: https://github.com/mraspaud/trollimage
.. _pycoast: https://github.com/mraspaud/pycoast 


Detailed instructions
=====================

.. toctree::
   :maxdepth: 3

   installation.rst
   configuration.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Trollduction
-------------

.. automodule:: trollduction.trollduction
   :members:
   :undoc-members:

Listener
-------------

.. automodule:: trollduction.listener
   :members:
   :undoc-members:

XML read
--------

.. automodule:: trollduction.xml_read
   :members:
   :undoc-members:

Helper functions
----------------

.. automodule:: trollduction.helper_functions
   :members:
   :undoc-members:

Custom handler
--------------

.. automodule:: trollduction.custom_handler
   :members:
   :undoc-members:
