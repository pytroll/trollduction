
======================================================
 Description and operation of the different processes
======================================================

Before any message-based processing, start the *posttroll* nameserver::

  $ cd /path/to/posttroll/bin
  $ ./nameserver

This script handles the connections between different message publishers and subscribers.


Trollstalker
============

Trollstalker is a script that monitors the arrival of given files in the
specified directories. When such a file is detected, a pytroll message is sent
on the network to notify other interested processes.

An example configuration file for trollstalker is provided in
`trollduction/examples/trollstalker.ini_template`:

.. literalinclude:: /../../examples/trollstalker.ini_template
   :language: ini

Of course, other sections can be added to the file for other files to be
watched.


In order to start *trollstalker*::

  $ cd trollduction/bin/
  $ ./trollstalker.py -c ../examples/trollstalker.ini -C noaa_hrpt

Now you can test if the messaging works by copying a data file to your input
directory. *Trollstalker* should send a message, and depending on the
configuration, also print the message on the terminal. If there's no message,
check the configuration files that the input directory and file pattern are set
correctly.


l2processor
===========

*l2processor* is the process that reads satellite data and generates composites
 from it. It is triggered by messages fullfilling a given topic, reads the data
 file, resamples the data to given areas and generates image composites.

Before starting to configure *l2processor*, make sure that your mpop_ has been
setup correctly (*mpop.cfg*, *areas.def*, satellite definitions). *l2processor*
relies heavily on `mpop`.

.. _mpop: http://mpop.readthedocs.org/en/latest/install.html#configuration

To configure *l2process*, the user needs to supply at least a configuration
files and a product list. The product list format is explained below.

An example configuration file for l2processor is provided in
`trollduction/examples/l2processor_config.ini_template`:

.. literalinclude:: /../../examples/l2processor_config.ini_template
   :language: ini


Start *l2processor* by::

  $ cd trollduction/bin/
  $ ./l2processor.py -c ../examples/master_config.ini -C noaa_hrpt


Product configuration file format
---------------------------------

The product list configuration file is an xml file that contains information
about the desired output of *l2processor*. An example file is provided in
`trollduction/examples/product_config_hrpt.xml_template`:

.. literalinclude:: /../../examples/product_config_hrpt.xml_template
   :language: xml


The first part, *<common>*, can be used to give default values that are used, if not overridden, by all the *<product>* definitions.

The second part is *<aliases>* and contains the substitutions to perform in the file patterns (from *src* to *dst*)

The third part is *<variables>* which holds the substitutions for the tag
attributes. Adding an attribute to *<variables>* checks if the corresponding
environment variable is set to the given value, and uses these substitutions if
it does.

The fourth part is the *<groups>* defining the area to group for processing. This means for example that the data will be loaded for the whole group (cutting at the area definition boundaries if supported). Setting th *unload* attribute to "true" provokes the unloading of the data before and after processing the group.

The next part is the *<product_list>* which contains the list of products and areas to work on.

The next layer of the product configuration is the *<area>*, which holds the following attributes:

* *name* --- replaces the *{areaname}* tag in the file name template
* *id* --- the name of the area/projection definition given in mpop areas.def file

The following layer is the *<product>* details to be produced in the area.
The *<product>* section is given for each product. These values override the defaults given (if any) in the *<common>* section.

Required attributes within *<product>*:

* *id* --- name of the function (from *mpop.image*) that produces the product
* *name* --- user-defined name for the composite, this will replace the *{productname}* tag in the file name pattern
* *overlay* --- the color of the overlay to put on the image, in hex hash
   (e.g. #ffffff for white) or alternatively the path to the overlay
   configuration file to pass to pycoast.
* *thumbnail_size* and *thumbnail_name* --- the size and filename of the thumbnail to produce. The thumbnail will be written in the same directory as the image.
* *sunzen_day_maximum* --- Sun zenith angle, can be used to limit the product to be generated only during sufficient lighting
* *sunzen_night_minimum* --- Sun zenith angle, can be used to limit the product to be generated only during sufficient darkness
* *sunzen_lonlat* --- comma-ceperated longitude and latitude values that can be used to define the location where Sun zenith angle values are checked. Only effective if either *sunzen_day_maximum* or *sunzen_night_minimum* is given.
* *sunzen_xy_loc* --- comma-ceperated x- and y-pixel coordinates that can be used to define the location where Sun zenith angle values are checked. Only effective if either *sunzen_day_maximum* or *sunzen_night_minimum* is given. Faster option for *sunzen_lonlat*, but needs to be determined separately for each area.

The final layer is the *<file>* tag which holds information of the file to be saved. It can have the following attributes:

* *output_dir* --- the destination directory
* *format* --- the file format to use. This is optional, but if the file format cannot be easily guessed from the file extension, it's good to write it here.
* The text of this *<file>* item is the filename pattern to use.

Data dumps
~~~~~~~~~~
An alternative to the *<product>* tag is the *<dump>* tag that saves the resampled data to the given filename (pattern). It can also be inserted at the previous layer to do a data dump of the unprojected data.

gatherer
========

Watches files or messages and gathers satellite granules in "collections",
sending then the collection of files in a message for further processing.

To be written


scisys_receiver
===============

Receive and translates scisys ground-station message to pytroll messages.

To be written

aapp_runner
===========

Run aapp

To be written

pps_runner
==========

Run pps

To be written

viirs_dr_runner
===============

Run viirs l0 -> l1 processor

To be written

modis_dr_runner
===============

Run modis l0 -> l1 processor

To be written
