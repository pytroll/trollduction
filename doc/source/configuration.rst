
===============
 Configuration
===============

Before starting to configure *trollduction*, make sure that your mpop_ has been setup correctly (*mpop.cfg*, *areas.def*, satellite definitions).

To configure *trollduction*, the user needs to supply atleast two configuration files. These files are explained below. The configuration file examples are available in *trolldcution/examples/* directory with *_template* ending. To use these, the files need to be renamed so that there is no word "template" within the filename.

Master config
-------------

The main configuration for *trollduction* processing chain defines the messaging, file patterns, satellite instrument name and configuration file locations for logging and product definitions (see below). The same configuration file is used for both *trollstalker* and *l2processor*. An example that can be used as a template is located in *trollduction/examples/master_config.ini_template*. Each different production chain can be placed in the same configuration file and are separated by *[chain_name]* header tag.

The required keys are:

* *service* --- name of the *trollstalker* service providing the messages for each new file. Also used by *l2processor* when subscribing for these messages
* *directory* --- full path to the directory receiving the new files
* *filepattern* --- file name pattern for the files, in trollsift_ format. The identifiers that will be parsed by *trollduction* are:
    * *path* --- directory path
    * *platform* --- satellite platform (eg. "noaa" or "MSG")
    * *satnumber* --- number of the satellite (eg. "19" of NOAA-19)
    * *time* --- data nominal time with datetime format attached "{time:%Y%m%d_%H%M}"
    * *orbit* --- orbit number of the polar-orbiting satellite
    * *instrument* --- instrument name given to GenericFactory of mpop_
* *product_config_file* --- full path to product configuration file, see the next section for product_ configuration

Optional configuration keys:

* *stalker_log_config* --- full path to logging configuration file for *trollstalker*
    * the output filename and path for *trollstalker* log files are set here
* *td_log_config* --- full path to logging configuration file for *trollduction*
    * the output filename and path for *trollduction* log files are set here
* *event_names* --- list of pyinotify event names that *trollstalker* will react to
* *posttroll_port* --- port number where posttroll messages are sent
* *timezone* --- Timezone that is used in log timestamps. Defaults to UTC.

The field lengths of *filepattern* can, and should when possible, be given::

{path}hrpt_{platform:4s}{satnumber:2d}_{time:%Y%m%d_%H%M}_{orbit:05d}.l1b

Here *path* holds everything that comes before "hrpt\_", *platform* is a character string of length 4, *satnumber* is a two-digit number, *time* has year, month and day followed by an underscore and hour and minutes, and *orbit* is a zero-padded number with five digits.

.. _trollsift: http://trollsift.readthedocs.org/en/latest/
.. _mpop: http://mpop.readthedocs.org/en/latest/


Product configuration file(s)
-----------------------------
.. _product:

Two examples for product configuration are supplied in *trollduction/examples/* directory:

* *product_config_hrpt.xml_template* for NOAA/AVHRR
* *product_config_hrit.xml_template* for Meteosat/SEVIRI

These files describe, in XML format, which image composites are made. Use these as a starting point for your own configuration, and save the file to the place set in your *master_config.ini* (without the *_template* ending!). The different parts and tags of the product configuration file are explained below. Notice that also *all* the corresponding closing tag is required (eg. *</common>*), and the file needs to be valid XML.

The first part, *<common>*, can be used to give default values that are used, if not overridden, by all the *<product>* definitions. Also, by defining *<netcdf_file>* in this section, the data in original satellite projection will be saved in netCDF4 format to the given filename.

The next layer of the product configuration is the *<area>*, which holds the following items:

* *<name>* --- replaces the *{areaname}* tag in the file name template
* *<definition>* --- the name of the area/projection definition given in mpop areas.def file
* *<product>* --- holds the details of each product to be generated for this area

The *<product>* section is given for each product. These values override the defaults given (if any) in the *<common>* section.

Required definitions within *<product>*:

* *<composite>* --- name of the function (from *mpop.image*) that produces the product
* *<name>* --- user-defined name for the composite, this will replace the *{composite}* tag in the file name pattern
* *<filename>* --- file name pattern to be used for saving the image. See example filename pattern at the end of the Master config section above. Optional, if the filename pattern is given in *<common>* section

Optional definitions:

* *<netcdf_file>* --- save the resampled data to the given filename (pattern)
* *<sunzen_day_maximum>* --- Sun zenith angle, can be used to limit the product to be generated only during sufficient lighting
* *<sunzen_night_minimum>* --- Sun zenith angle, can be used to limit the product to be generated only during sufficient darkness
* *<sunzen_lonlat>* --- comma-ceperated longitude and latitude values that can be used to define the location where Sun zenith angle values are checked. Only effective if either *<sunzen_day_maximum>* or *<sunzen_night_minimum>* is given.
* *<sunzen_xy_loc>* --- comma-ceperated x- and y-pixel coordinates that can be used to define the location where Sun zenith angle values are checked. Only effective if either *<sunzen_day_maximum>* or *<sunzen_night_minimum>* is given. Faster option for *<sunzen_lonlat>*, but needs to be determined separately for each area.

