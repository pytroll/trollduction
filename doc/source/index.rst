.. trollduction documentation master file, created by
   sphinx-quickstart on Mon Feb 17 08:35:12 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to trollduction's documentation!
========================================

Trollduction is a configurable framework for satellite image production.

This documentation is a work in progress, so most of the details are missing.  Below you can find short instructions how to get started.

The source code of the package can be found at github_

.. _github: https://github.com/mraspaud/trollduction


Setting things up, the simple version
=====================================

1. Install other required packages
    * mpop_ - *pre-master* branch
    * pyresample_
    * posttroll_ - *feature_service* branch
    * pyorbital_
    * trollsift_
    * python-lxml
    * python-pyinotify
2. Configure mpop
    * modify *mpop.cfg* to suit your needs
    * add configurations for satellites you are going to use
3. Create Trollduction configuration file
    * use *examples/master_config.ini* as a template
4. Create Trollduction product configuration file
    * use *trollduction/etc/product_config_hrpt.xml* or *trollduction/etc/product_config_hrpt.xml* as a template
    * save the file to the path defined in your *master_config.ini*
5. Start *posttroll/bin/nameserver*
    * this will relay the messages sent in the network
    * *./nameserver*
6. Start *trollduction/bin/trollstalker.py*
    * file watcher that sends a message of new files
    * for example: *./trollstalker.py -c ../examples/master_config.ini noaa_hrpt*
7. Start Trollduction *trollduction/bin/l2processor.py*
    * *./l2processor.py ../examples/master_config.ini noaa_hrpt*
    * this should print your configuration and stop to wait for new
      messages
8. Copy a suitable file to your data input directory
9. Check the output directory for images

.. _mpop: https://github.com/mraspaud/mpop
.. _pyresample: https://code.google.com/p/pyresample/
.. _posttroll: https://github.com/mraspaud/posttroll
.. _pyorbital: https://github.com/mraspaud/pyorbital
.. _trollsift: https://github.com/pnuu/trollsift

Contents:
=========

.. toctree::
   :maxdepth: 2

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

Trollstalker
-------------

.. automodule:: trollduction.trollstalker
   :members:
   :undoc-members:

Listener
-------------

.. automodule:: trollduction.listener
   :members:
   :undoc-members:

Logger
-------------

.. automodule:: trollduction.logger
   :members:
   :undoc-members:
