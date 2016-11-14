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


Setting things up cheat sheet
=============================

1. Install other required packages:
    * libnetcdf-dev
    * libhdf5-dev
    * python-numpy
    * python-zmq
    * python-pyinotify

   and the Pytroll packages:

    * pytroll-collectors_
    * mpop_
    * mipp_
    * pyresample_
    * posttroll_
    * pyorbital_
    * trollsift_
    * trollduction_
    * pytroll-schedule_
    * pyspectral_
    * pykdtree_
    * python-geotiepoints_
    * trollimage_
    * pycoast_

#. Configure mpop
    * modify *mpop.cfg* to suit your needs
    * add configurations for satellites you are going to use (see the templates
      in `mpop/etc/`)
#. Create Trollduction configuration files
    * use *trollduction/examples/trollstalker_config.ini_template* as a template
    * use *trollduction/examples/l2processor_config.ini_template* as a template
    * save config file to your chosen place without the *_template* ending
#. Create Trollduction product configuration file
    * use *trollduction/examples/product_config_hrpt.xml_template* as a template
    * save the file to the path defined in your *l2processor_config.ini*
      without the *_template* ending
    * define your output_dir in the xml file
    * topic from the *trollstalker_config.ini* must be included in the list
      of topics in *l2processor_config.ini*
#. Create logging configurations for *trollduction* and *trollstalker*
    * *trollstalker* is part of *pytroll-collectors* package
    * use *trollduction/examples/l2processor_logging.ini_template* and
      *pytroll-collectors/examples/trollstalker_logging.ini_template* as templates
    * check the log filename (by default logs go to */tmp/* directory)
    * save these configs to the path defined in your *l2processor_config.ini*
      and *trollstalker_config.ini* without the *_template* ending
#. Start *posttroll/bin/nameserver*
    * this will register the different subscribers on the network and relay the
      messages between different processes
    * *./nameserver*
#. Start *pytroll-collectors/bin/trollstalker.py*
    * file watcher that sends messages of new files available for processing
    * for example: *./trollstalker.py -c /path/to/trollstalker_config.ini
      -C noaa_hrpt*
#. Start Trollduction *trollduction/bin/l2processor.py*
    * *./l2processor.py -c /path/to/l2processor_config.ini -C noaa_hrpt*
    * this should print your configuration and stop to wait for new
      messages
#. Copy a suitable file to your data input directory
#. Check the output directory for images

.. _pytroll-collectors: https://github.com/pytroll/pytroll-collectors
.. _mpop: https://github.com/pytroll/mpop
.. _mipp: https://github.com/pytroll/mipp
.. _pyresample: https://github.com/pytroll/pyresample
.. _posttroll: https://github.com/pytroll/posttroll
.. _pyorbital: https://github.com/pytroll/pyorbital
.. _trollsift: https://github.com/pytrol/trollsift
.. _trollduction: https://github.com/pytroll/trollduction
.. _pytroll-schedule: https://github.com/pytroll/pytroll-schedule
.. _pyspectral: https://github.com/pytroll/pyspectral
.. _pykdtree: https://github.com/storpipfugl/pykdtree
.. _python-geotiepoints: https://github.com/pytroll/python-geotiepoints
.. _trollimage: https://github.com/pytroll/trollimage
.. _pycoast: https://github.com/pytroll/pycoast 


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
