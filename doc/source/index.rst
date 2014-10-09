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

Setting things up cheat sheet
=============================

1. Install other required packages
    * mpop_ - select *pre-master* branch
    * pyresample_
    * posttroll_ - select *feature_service* branch
    * pyorbital_
    * trollsift_
    * python-pyinotify
    * trollduction_ - select *develop* branch
#. Configure mpop
    * modify *mpop.cfg* to suit your needs
    * add configurations for satellites you are going to use
#. Create Trollduction configuration file
    * use *examples/master_config.ini_template* as a template
    * save config file to your chosen place without the *_template* ending
#. Create Trollduction product configuration file
    * use *trollduction/examples/product_config_hrpt.xml_template* or *trollduction/examples/product_config_hrpt.xml_template* as a template
    * save the file to the path defined in your *master_config.ini* without the *_template* ending
#. Create logging configurations for *trollduction* and *trollstalker*
    * use *trollduction/examples/td_logging.ini_template* and *trollduction/examples/stalker_logging.ini_tempalate* as templates
    * check the log filename (by default logs go to */tmp/* directory)
    * save these configs to the path defined in you *master_config.ini* without the *_template* ending
#. Start *posttroll/bin/nameserver*
    * this will relay the messages sent in the network
    * *./nameserver*
#. Start *trollduction/bin/trollstalker.py*
    * file watcher that sends messages of new files available for processing
    * for example: *./trollstalker.py -c /path/to/master_config.ini -C noaa_hrpt*
#. Start Trollduction *trollduction/bin/l2processor.py*
    * *./l2processor.py -c /path/to/master_config.ini -C noaa_hrpt*
    * this should print your configuration and stop to wait for new
      messages
#. Copy a suitable file to your data input directory
#. Check the output directory for images

.. _mpop: https://github.com/mraspaud/mpop
.. _pyresample: https://code.google.com/p/pyresample/
.. _posttroll: https://github.com/mraspaud/posttroll
.. _pyorbital: https://github.com/mraspaud/pyorbital
.. _trollsift: https://github.com/pnuu/trollsift
.. _trollduction: https://github.com/mraspaud/trollduction

Detailed instructions
=====================

.. toctree::
   :maxdepth: 3

   installation.rst
   configuration.rst
   usage.rst

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

Duke
----

.. automodule:: trollduction.duke
   :members:
   :undoc-members:

Minion
------

.. automodule:: trollduction.minion
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
