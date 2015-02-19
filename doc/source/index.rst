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
 - l2processor: generates rgb images when an appropriate event message is
   received
 - gatherer: gathers polar satellite granules together given an area of
   interest, and send an event messages when a matching group of granules has
   been gathered
 - aapp_runner: runs the NWP-AAPP software on raw hrpt files, when such an event
   message is received, to generate level 1 data
 - viirs_dr_runner: runs the CSPP software on Suomi-NPP RDR files to generate
   level 1 data
 - modis_dr_runner: runs the SPA software on EOS-Terra/Aqua PDS files to
   generate level 1 data


Setting things up cheat sheet
=============================

1. Install other required packages
    * mpop_ - select *pre-master* branch
    * pyresample_
    * posttroll_ - select *develop* branch
    * pyorbital_
    * trollsift_
    * python-pyinotify
    * trollduction_ - select *feature-aapp-and-npp* branch
    * pytroll-schedule_ - select *develop* branch
#. Configure mpop
    * modify *mpop.cfg* to suit your needs
    * add configurations for satellites you are going to use
#. Create Trollduction configuration files
    * use *examples/trollstalker_config.ini_template* as a template
    * use *examples/l2processor_config.ini_template* as a template
    * save config file to your chosen place without the *_template* ending
#. Create Trollduction product configuration file
    * use *trollduction/examples/product_config_hrpt.xml_template* as a template
    * save the file to the path defined in your *l2processor_config.ini* without the *_template* ending
#. Create logging configurations for *trollduction* and *trollstalker*
    * use *trollduction/examples/td_logging.ini_template* and *trollduction/examples/stalker_logging.ini_tempalate* as templates
    * check the log filename (by default logs go to */tmp/* directory)
    * save these configs to the path defined in you *l2processor_config.ini* and *trollstalker_config.ini* without the *_template* ending
#. Start *posttroll/bin/nameserver*
    * this will register the different components on the network
    * *./nameserver*
#. Start *trollduction/bin/trollstalker.py*
    * file watcher that sends messages of new files available for processing
    * for example: *./trollstalker.py -c /path/to/trollstalker_config.ini -C noaa_hrpt*
#. Start Trollduction *trollduction/bin/l2processor.py*
    * *./l2processor.py -c /path/to/l2processor_config.ini -C noaa_hrpt*
    * this should print your configuration and stop to wait for new
      messages
#. Copy a suitable file to your data input directory
#. Check the output directory for images

.. _mpop: https://github.com/mraspaud/mpop
.. _pyresample: https://code.google.com/p/pyresample/
.. _posttroll: https://github.com/mraspaud/posttroll
.. _pyorbital: https://github.com/mraspaud/pyorbital
.. _pytroll-schedule: https://github.com/mraspaud/pytroll-schedule
.. _trollsift: https://github.com/pnuu/trollsift
.. _trollduction: https://github.com/mraspaud/trollduction

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
