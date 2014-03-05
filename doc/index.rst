.. trollduction documentation master file, created by
   sphinx-quickstart on Mon Feb 17 08:35:12 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to trollduction's documentation!
========================================

Trollduction is a configurable framework for satellite image production.

This documentation is a work in progress, so most of the details are
missing.  Below you can find short instructions how to get started.

Setting things up
=================

1. Install other required packages
    * [mpop](https://github.com/mraspaud/mpop) - *pre-master* branch
    * [pyresample](https://code.google.com/p/pyresample/)
    * [posttroll](https://github.com/mraspaud/posttroll) - *develop* branch
    * [pyorbital](https://github.com/mraspaud/pyorbital)
    * python-lxml
    * python-pyinotify
2. Configure mpop
    * modify *mpop.cfg* to suit your needs
    * add configurations for satellites you are going to use
3. Create Trollduction configuration file
    * use *trollduction/etc/trollduction_config.xml* as a template
4. Create Trollduction product configuration file
    * use *trollduction/etc/product_config.xml* as a template
    * save the file to the path defined in your *trollduction_config.xml*
5. Start *posttroll/bin/nameserver*
    * this will relay the messages sent in the network
    * *./nameserver*
6. Start *trollduction/bin/trollstalker.py*
    * file watcher that sends a message of new files
    * for example: *./trollstalker.py -m hrpt - t HRPT_l1b -t
      /data/incoming/*
        * *-m*: filepattern to watch, here hrpt*
        * *-t*: type of the message to be sent.  Use the same value as
          set in your *trollduction_config.xml* with
          *<listener_tag></listener_tag>* tags
        * *-d*: directory where new files are coming.  Use the same
          value as set in your *mpop* satellite configurations with
          tag *dir*.
7. Start Trollduction *trollduction/bin/main.py*
    * *./main.py /full/path/to/trollduction_config.xml*
    * this should print your configuration and stop to wait for new
      messages
8. Copy a suitable file to your data input directory
9. Check the output directory for images


Contents:
=========

.. toctree::
   :maxdepth: 2

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
