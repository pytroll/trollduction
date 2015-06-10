Usage
=====

To run *trollduction*, several different scripts needs to be run. Below you can find the order and commands that need to be issued. These commands show how to run the batch processing in testing. For clarity, open a new terminal window for each part. For operational use a more robust start-up system, eg. supervisord_, is preferable.

.. _supervisord: http://supervisord.org/

nameserver
----------

First step is to start the *posttroll* nameserver::

  $ cd /path/to/posttroll/bin
  $ ./nameserver

This script handles the connections between different message publishers and subscribers.

trollstalker
------------

Start *trollstalker*::

  $ cd trollduction/bin/
  $ ./trollstalker.py -c ../examples/trollstalker_config.ini -C noaa_hrpt

Now you can test if the messaging works by copying a data file to your input directory. *Trollstalker* should send a message, and depending on the configuration, also print the message on the terminal. If there's no message, check the configuration files that the input directory and file pattern are set correctly.

l2processor
-----------

The *main* command that actually runs *trollduction* is called *l2processor.py*. This reads the main configuration file and initializes *trollduction*, which in turn waits for messages from *trollstalker*. When a message is received, *trollduction* reads the data, resamples the data to given area(s) and generates the image composites.

Start *l2processor* by::

  $ cd trollduction/bin/
  $ ./l2processor.py -c ../examples/l2processor_config.ini -C noaa_hrpt

Now copy a file to the input directory, and the production should start and the terminal should show lots of text. After the file has been processed, check the image output directory for the products.

