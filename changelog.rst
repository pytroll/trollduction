Changelog
=========

v0.2.0 (2015-02-19)
-------------------

Fix
~~~

- Bugfix: error message in image generation was buggy. [Martin Raspaud]

- Bugfix: variable substitution. [Martin Raspaud]

- Bugfix: unload after channel names. [Martin Raspaud]

- Bugfix: the unloading doesn't work on a list, * it. [Martin Raspaud]

- Bugfix: Error was shutil.Error. [Martin Raspaud]

- Bugfix: instrument is now called sensor. [Martin Raspaud]

- Bugfix: add missing dependency. [Martin Raspaud]

- Bugfix: don't check host for local files. [Martin Raspaud]

- Bugfix: remove last traces of minion. [Martin Raspaud]

- Bugfix: sleep forever in trollstalker now... [Martin Raspaud]

Other
~~~~~

- Update changelog. [Martin Raspaud]

- Bump version: 0.1.0 → 0.2.0. [Martin Raspaud]

- Change version numbering. [Martin Raspaud]

- Some more documentation. [Martin Raspaud]

- Update the documentation a bit. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Simplified the code. [Adam Dybbroe]

- Really kill the idle process. [Adam Dybbroe]

- Replace the corner estimation in region_collector with trollsched's
  routines. [Martin Raspaud]

- Install mock for travis. [Martin Raspaud]

- Change publisher name for gatherer to "gatherer". [Martin Raspaud]

- L2processor: print out reason when trollduction dies. [Martin Raspaud]

- Install hdf5 and netcdf on travis before testing. [Martin Raspaud]

- Add missing dependencies. [Martin Raspaud]

- Add pytroll-schedule as dependency. [Martin Raspaud]

- Handling IOError excpetion in copy file ("Stale file handle") [Adam
  Dybbroe]

- Try fixing a bug in an exception. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Identifying pps jobs by time as well, and don't do repeated processing
  on scenes that are close in time. [Adam Dybbroe]

- More debug info. [Adam Dybbroe]

- Fixing Metop names for tle files. [Adam Dybbroe]

- More debug info. [Adam Dybbroe]

- Moving common function from aapp_runner to helper_functions. [Adam
  Dybbroe]

- More log info. [Adam Dybbroe]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

  Conflicts:
  	bin/trollstalker.py

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

  Conflicts:
  	bin/trollstalker.py


- Add orbit style flag for have consistent orbit numbers in the system.
  [Martin Raspaud]

- Derive orbit number in aapp runner. [Adam Dybbroe]

- Handling more than one instrument in config file. [Adam Dybbroe]

- Bugfix and more debug info. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- More debug info. [Adam Dybbroe]

- Bugfix again... [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Bugfixing and cleaning up a bit in aapp-runner. [Adam Dybbroe]

- Adding template for pps-run script. [Adam Dybbroe]

- Adapting to new pps bash script, where no date/time is provided for
  other satellites than EOS. [Adam Dybbroe]

- Allowing aapp to run also on DMI data. [Adam Dybbroe]

- Fix thumbnail_size type when generating error message. [Martin
  Raspaud]

- Pps_runner now publishes h5 files instead. [Martin Raspaud]

- Try bug fixing debug printout... [Adam Dybbroe]

- Remove all shell=True from Popen calls. [Adam Dybbroe]

- Bugfix... [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Bugfix... [Adam Dybbroe]

- Popen tests... [Adam Dybbroe]

- Using shlex to construct Popen arguments. [Adam Dybbroe]

- Changing Popen calls... [Adam Dybbroe]

- Shell=True (going back, since shell=False didn't work) [Adam Dybbroe]

- Set working dir for Aqua gbad processing! [Adam Dybbroe]

- Check the status code from the MODIS lvl1 processing and only continue
  if it is equal "0" [Adam Dybbroe]

- Add more log info. [Adam Dybbroe]

- Restructure modis runner for standardised logging. [Adam Dybbroe]

- Remove unnecessary tle handling. [Martin Raspaud]

- Remove unnecessary hardcoded global variables and config items.
  [Martin Raspaud]

- Print out viirs config file on running. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Add more debug info. [Adam Dybbroe]

- Adding module name to log. [Adam Dybbroe]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Changed logging format for modis, and fixed symlink bug. [Adam
  Dybbroe]

- Use command-line parameters for viirs_dr_runner. [Martin Raspaud]

- On linking error, tell which files are failing. [Martin Raspaud]

- Allow reading configuration for pycoast. [Martin Raspaud]

- Updating the documentation. [Martin Raspaud]

- Add coverage functionality for geostationary data. [Martin Raspaud]

- Gatherer: add the possibility to choose which observer is being used.
  [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Revert "Go back to 'old' modis_dr_runner from mid November" [Adam
  Dybbroe]

  This reverts commit c6e1f0e5047eb780b71af56364446000c755507e.


- Go back to 'old' modis_dr_runner from mid November. [Adam Dybbroe]

- Change the subscription. [Adam Dybbroe]

- Remove modis script from bin. [Adam Dybbroe]

- Update documentation. [Martin Raspaud]

- Remove area coverage computation if no overpass attribute is present.
  [Martin Raspaud]

- Bugfix trollstalker: the file parsing is now occuring on the basename.
  [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Debug info added. [Adam Dybbroe]

- Adapted to modis_runner. [Adam Dybbroe]

- Fixing modis_runner. [Adam Dybbroe]

- Trollstalker improvements to avoid wrong error catching. [Martin
  Raspaud]

- Check for local ips with netifaces (should be more robust) [Martin
  Raspaud]

- Receive RDRs from any publisher. [Martin Raspaud]

- Add a working dir for modis gbad processing. [Martin Raspaud]

- Fix trollstalker to new metadata. [Martin Raspaud]

- Report error on KeyError for product_config_file. [Martin Raspaud]

- Add modis_runner.py. [Martin Raspaud]

- "variables" now accepts environment variables to check against.
  [Martin Raspaud]

- Allow specifying overlay="#<color>" in xml product list. [Martin
  Raspaud]

- Bugfix thumbnailing. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Allow to listen for everything publishing level 1 files. [Adam
  Dybbroe]

- Add thumbnailing functionality. [Martin Raspaud]

- Add a time_interval load argument if possible. [Martin Raspaud]

- Do not create satellite scenes with multiple sensors. [Martin Raspaud]

- Allow multiple sensors in message. [Martin Raspaud]

- Coverage computation is now done at the group level to avoid unloading
  if possible. [Martin Raspaud]

- Print out linking exceptions. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Bugfix, for metop. [Adam Dybbroe]

- More debug info in aapp runner. [Adam Dybbroe]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Correcting the name of the runner publishing. [Adam Dybbroe]

- Fix multiple Thread inheritance. [Martin Raspaud]

- Groups can now have "unload" and "resolution" parameters. [Martin
  Raspaud]

- Do not crash when copying goes wrong. [Martin Raspaud]

- Scale coverages to the same magnitude order. [Martin Raspaud]

- Add coverage computation. [Martin Raspaud]

- Fix copy to itself. [Martin Raspaud]

- Make orbit number an int when sending out messages. [Martin Raspaud]

- Comments added. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Level 1 data dir is set outside PPS. [Adam Dybbroe]

- Add aliases possibility in the product list and copy files when
  already saved. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Adapting PPS for collections. [Adam Dybbroe]

- Remove platform name translation. [Martin Raspaud]

- Move check_uri out of the dataprocessor class. [Martin Raspaud]

- Mock out entire watchdogtrigger on importerror. [Martin Raspaud]

- Mock watchdog if not present. [Martin Raspaud]

- Catch importerrors when watchdog is imported. [Martin Raspaud]

- Add collectors in setup.py. [Martin Raspaud]

- Add the collector __init__.py. [Martin Raspaud]

- Move gatherer to bin. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Bugfix, sensor naming. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- More consistency in platform name handling. [Adam Dybbroe]

- Bugfix - published satellite name. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Fix metadata in output messages from pps. [Adam Dybbroe]

- Handle collections in producer. [Martin Raspaud]

- Fix gatherer and regioncollector for new metadata and npp granules.
  [Martin Raspaud]

- Add PostTrollTrigger to triggers. [Martin Raspaud]

- Switch SDR to level 1b (instead of 1) [Martin Raspaud]

- Log exception in case of incomplete or corrupted data. [Martin
  Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Bugfix sensor naming. [Adam Dybbroe]

- Do not publish messages if no sdr files are created. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Bugfix. [Adam Dybbroe]

- Change viirs_dr_runner to send batch of files as datasets. [Martin
  Raspaud]

- Remove non-existant scripts from setup. [Martin Raspaud]

- Add some debugging messages around data loading. [Martin Raspaud]

- Remove smhi scripts. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Installs aapp runner. [Adam Dybbroe]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Aapp config template (from smhi) [Adam Dybbroe]

- Add the (smhi) aapp_runner.py. [Adam Dybbroe]

- Consistent metop/noaa sensor names. [Adam Dybbroe]

- Smoother crashing of producer.py. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Bugfix - orbit. [Adam Dybbroe]

- Bugfix - instrument->sensor. [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Install pps scripts. [Adam Dybbroe]

- Adding pps runner. [Adam Dybbroe]

- Fix sensor=modis in published messages. [Adam Dybbroe]

- Bugfix! Arggghh! [Adam Dybbroe]

- Adding helper function to create (aqua) messages from receiver log for
  later ingestion. [Adam Dybbroe]

- More debugging. [Adam Dybbroe]

- Add debug info. [Adam Dybbroe]

- Bugfix EOS-Aqua name... [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Debug info and pep8. [Adam Dybbroe]

- Renamed modis_runner function not to be confused with modulename.
  [Adam Dybbroe]

- More deug info - message creation is at error! [Adam Dybbroe]

- Bugfix. [Adam Dybbroe]

- Less verbose. [Adam Dybbroe]

- Adapt to new message format. [Adam Dybbroe]

- GPL header added. [Adam Dybbroe]

- Npp/viirs bugfixes. [Adam Dybbroe]

- Producer adaptation to "dataset" messages. [Martin Raspaud]

- Allow to run l2proc on several topics. [Martin Raspaud]

- Bugfix modis. [Martin Raspaud]

- Fix instrument->sensor. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Fix installation of npp-stuff. [Adam Dybbroe]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Adding template for viirs. [Adam Dybbroe]

- Adding S-NPP VIIRS runner. [Adam Dybbroe]

- Send datasets for modis l1b files. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Bugfix. [Adam Dybbroe]

- Moving smhi'fied script to a template/example. [Adam Dybbroe]

- Remove smhi stuff. [Adam Dybbroe]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Adam
  Dybbroe]

- Merge branch 'smhi-develop' of /data/proj/SAF/GIT/trollduction into
  feature-aapp-and-npp. [Adam Dybbroe]

- Merge branch 'feature-aapp-and-npp' into smhi-develop. [Martin
  Raspaud]

  Conflicts:
  	setup.py

- Add pyinotify to the list of dependencies. [Martin Raspaud]

- Fixing setup for SMHI. [Martin Raspaud]

- Change modis runner to accept new metadata standard. [Martin Raspaud]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

- Bugfix, and comment away broken tests! [Adam Dybbroe]

- Adding the modis-dr-runner from smhi. [Adam Dybbroe]

- Add orbit_number for NPP rdrs. [Martin Raspaud]

- Bugfix scisys: satellite is not always defined for npp rdrs. [Martin
  Raspaud]

- Add the scisys library. [Martin Raspaud]

- Add scisys_receiver.py to scripts. [Martin Raspaud]

- Update producer for new metadata standard. [Martin Raspaud]

- Add scisys test to test bench. [Martin Raspaud]

- Change description in setup.py. [Martin Raspaud]

- Add scisys receiver. [Martin Raspaud]

- Implement area groups. [Martin Raspaud]

- Metadata adjustments. [Martin Raspaud]

- Import AreaNotFound error. [Martin Raspaud]

- Don't crash on area not found. [Martin Raspaud]

- Set orbit number as string. [Martin Raspaud]

- Various fixes. [Martin Raspaud]

- Fix unittest. [Martin Raspaud]

- Do not crash when composite is not available for satellite. [Martin
  Raspaud]

- Cleanup. [Martin Raspaud]

- Logging and argparsing in catter. [Martin Raspaud]

- Add example files for gatherer and catter. [Martin Raspaud]

- Remove hardcoded link to configuration files. [Martin Raspaud]

- Accept collections in producer. [Martin Raspaud]

- Granule handling, first commit. [Martin Raspaud]

  * Region collection is implemented.
  * catter cats the low level data.

- Implemented variable substitution in xml product lists. [Martin
  Raspaud]

- Try to fix unittest. [Martin Raspaud]

- Add publishing of generated files. [Martin Raspaud]

- Refactoring to allow multiple files per product, among other things.
  [Martin Raspaud]

- Bugfix for integer satellite numbers. [Martin Raspaud]

- Orbit is now orbit_number in config files. [Martin Raspaud]

- Test mock nc/cf. [Martin Raspaud]

- Mock trollsift in test. [Martin Raspaud]

- Producer refactoring and netcdf revamping to avoid race condition.
  [Martin Raspaud]

- Change 'orbit' to 'orbit_number' [Martin Raspaud]

- Add trollsift to the list of dependencies. [Martin Raspaud]

- Add pyorbital to the list of dependencies. [Martin Raspaud]

- Add pykdtree and trollimage to the list of dependencies. [Martin
  Raspaud]

- Add pyresample to the list of dependencies. [Martin Raspaud]

- Add posttroll to the list of dependencies. [Martin Raspaud]

- Add mpop to the list of dependencies. [Martin Raspaud]

- First test for run should be complete. [Martin Raspaud]

- Rename orbit parameter to orbit_number. [Martin Raspaud]

- Add trollduction unittest skeleton. [Martin Raspaud]

- New xml format. [Martin Raspaud]

- Rename trollduction.py to producer.py to avoid confusion with package
  name. [Martin Raspaud]

- Merge remote branch 'origin/develop' into feature-aapp-and-npp.
  [Martin Raspaud]

  Conflicts:
  	trollduction/trollduction.py


- Renamed config item "service" to "topic" [Panu Lahtinen]

- Added try/except blocks to make the production more robust, changed
  config item "service" to "topic" [Panu Lahtinen]

- Removed references to lxml which is not used anymore. [Panu Lahtinen]

- Removed the need for lxml, use the standard lib xml.etree.ElementTree
  instead. [Panu Lahtinen]

- Fixed errors in example configs, updated the message for reading
  product config. [Panu Lahtinen]

- Merge branch 'feature-aapp-and-npp' of
  github.com:mraspaud/trollduction into feature-aapp-and-npp. [Martin
  Raspaud]

  Conflicts:
  	trollduction/trollduction.py


- Support messages with satellite instead of platform and number.
  [Martin Raspaud]

- Support messages with satellite instead of platform and number.
  [Martin Raspaud]

- Get the time from different possible tags. [Martin Raspaud]

- Remove annoying Minion parent, doesn't make sense with supervisord.
  [Martin Raspaud]

- Pep8 style corrections. [Martin Raspaud]

- Load the filename provided in the message if possible. [Martin
  Raspaud]

- Check if file is on the localhost before running. [Martin Raspaud]

- Add pyinotify to the install dependencies. [Martin Raspaud]

- Added "aliases" for replacing values in messages. [Panu Lahtinen]

- Requirements file for Read the Docs. [Panu Lahtinen]

- Fixed a type in "Sun too low night-only product" [Panu Lahtinen]

- Escape a part that ReST interpreted as a target (link) [Panu Lahtinen]

- Moved also template product configs to *_template filenames. [Panu
  Lahtinen]

- Possibility to change timezone for log timestamps (default: UTC),
  updated/fixed documentation, install bin/*.py, moved config templates
  to examples/, config files to *.ini_template, config files with
  _template ending can't be used. [Panu Lahtinen]

- Updated documentation. [Panu Lahtinen]

- Removed log_dir config item, which is not used. [Panu Lahtinen]

- Few updates to documentation. [Panu Lahtinen]

- Use unified configuration file for trollstalker and l2processor,
  removed deprecated files and added example/master_config.ini to show
  two examples how the configuration is made. [Panu Lahtinen]

- Deleted depracated config for filepatterns. [Panu Lahtinen]

- Changed to use posttroll NSSubscriber keyword 'service' instead of old
  data_type_list. [Panu Lahtinen]

- Reorganized and added missing keywords. [Panu Lahtinen]

- Reorganized items and added missing keywords. [Panu Lahtinen]

- Added config_item keyword. [Panu Lahtinen]

- Added 'instrument' config option and propagate this info to message.
  [Panu Lahtinen]

- Moved to examples/procuct_config_hrit.xml. [Panu Lahtinen]

- Example product configs for NOAA/AVHRR HRPT/AAPP/l1b and MSG/HRIT.
  [Panu Lahtinen]

- Removed deprecated config file. [Panu Lahtinen]

- Trollduction config in config.ini format. [Panu Lahtinen]

- Use trollsift.Parser to generate filenames. [Panu Lahtinen]

- Added a possibility to read config.ini format. [Panu Lahtinen]

- Fixes to syntax. [Panu Lahtinen]

- Merge remote-tracking branch 'origin/feature_parser_stalker' into
  develop. [Panu Lahtinen]

  Conflicts:
  	bin/main.py
  	bin/trollstalker.py

  Conflicts resolved.


- Syntactical cleanup. [Panu Lahtinen]

- Log config for trollstalker. [Panu Lahtinen]

- File pattern and logging.cfg. [Panu Lahtinen]

- Deleted empty file. [Panu Lahtinen]

- Deleted obsolete xml-config. [Panu Lahtinen]

- Changed to use trollsift.Parser for getting information from files,
  changed to config.ini format. TODO: using config doesn't work! [Panu
  Lahtinen]

- Example configuration file for trollstalker in config.ini format.
  [Panu Lahtinen]

- Merge remote-tracking branch 'origin/feature_xrit_extent' into
  develop. [Panu Lahtinen]

  Conflicts:
  	trollduction/custom_handler.py
  	trollduction/trollduction.py

  Conflicts resolved.


- Converted to use area extent calculations based on the area definition
  borders instead of lonlat corner points. [Panu Lahtinen]

- Removed disable_data_reduce config keyword. [Panu Lahtinen]

- Removed handling of disable_data_reduce config keyword. [Panu
  Lahtinen]

- GEO extent calculations moved to mpop, data reduction (for swath data)
  moved to mpop. [Panu Lahtinen]

- Added get_maximum_ll_borders() [Panu Lahtinen]

- Added <disable_data_reduce> [Panu Lahtinen]

- Moved OldTrollduction to own file old_trollduction.py. [Panu Lahtinen]

- Adjusted to use old_trollduction.OldTrollduction. [Panu Lahtinen]

- Moved older version of trollduction to own file. Also, implemented
  area extent for any area definition (regardless of projection) for
  MSG, and data reduction for polar satellites. [Panu Lahtinen]

- Moved common functions to own file. [Panu Lahtinen]

- Syntactical cleanup. [Panu Lahtinen]

- Syntactic cleanup. [Panu Lahtinen]

- Removed obsolete publisher/logger. [Panu Lahtinen]

- Support for getting maximum extent in lon/lat. Useable with MSG(3),
  and shouldn't break polar satellite production. [Panu Lahtinen]

- Merge remote-tracking branch 'origin/feature-duke' into develop. [Panu
  Lahtinen]

  Conflicts:
  	bin/trollstalker.py

  Conflict fixed.


- Tweaks for get_lan_ip() [Panu Lahtinen]

- Working version to test-run OldTrollduction. [Panu Lahtinen]

- Add poking. [Martin Raspaud]

- Work on dungeon keeper. [Martin Raspaud]

- Refactor trollduction. [Martin Raspaud]

- Removed deprecated publisher/logger. [Panu Lahtinen]

- More notation cleanup. [Panu Lahtinen]

- Notation cleanup. [Panu Lahtinen]

- Merge branch 'feature_config' into develop. [Martin Raspaud]

- Added IN_MOVED_TO and a commandline switch for enabling debug
  messages. [Panu Lahtinen]

- Remove old print messages. [Martin Raspaud]

- Panu's custom handler. [Martin Raspaud]

- Cleanup. [Martin Raspaud]

- Logging now uses a standard config file. [Martin Raspaud]

- Cleanup. [Martin Raspaud]

- Switch to standard logging with a pytroll handler. [Martin Raspaud]

- Removed debug print IN_CLOSE_WRITE. [Panu Lahtinen]

- Removed unneeded events. [Panu Lahtinen]

- Changed has_key to "in" [Panu Lahtinen]

- Removed unnecessary import of sys. [Panu Lahtinen]

- Changed has_key() to in. [Panu Lahtinen]

- Fix for conflicting member names. [Panu Lahtinen]

- Possibility to use select local or UTC time (default) for logging in
  trollduction_config.xml (<use_local_time>1</use_local_time>) [Panu
  Lahtinen]

- Fixed incorrect event IN_MOVED_IN to IN_MOVED_TO. [Panu Lahtinen]

- Changed to use Queue.Queue instead of mutliprocessing.Pipe for message
  passing, and made the program cleanly stoppable by ctrl+c. [Panu
  Lahtinen]

- Changed to use Queue.Queue instead of multiprocessing.Pipe for
  handling message passing. [Panu Lahtinen]

- Added clean stopping for Publisher. [Panu Lahtinen]

- Better event masking using bit-wise or. [Panu Lahtinen]

- Fixed --monitored_dirs commandline switch. [Panu Lahtinen]

- Removed old logger. [Panu Lahtinen]

- Example config for trollstalker. [Panu Lahtinen]

- Now using new logger/publisher with 60 s heartbeat. [Panu Lahtinen]

- New logger/publisher. [Panu Lahtinen]

- Removed references to old logger. [Panu Lahtinen]

- In trollstalker, command line args take precedence. Missing config
  file doesn't crash. [Martin Raspaud]

- Log&publish listener readiness. [Panu Lahtinen]

- Removed unnecessary print. [Panu Lahtinen]

- Logging and placeholder for message publishing. [Panu Lahtinen]

- Clarifications to check_sunzen() [Panu Lahtinen]

- Sun zenith-angle limits can be checked with pixel location given in
  product configuration file. [Panu Lahtinen]

- Sun zenith angle limits can be checked against configured location
  (lon, lat) [Panu Lahtinen]

- Empty line removed. [Panu Lahtinen]

- Possibility to add integer to xml value. [Panu Lahtinen]

- Check for orbit=None. [Panu Lahtinen]

- Separated MSG2 (Meteosat 9) and MSG3 (Meteosat 10) [Panu Lahtinen]

- Template for trollduction file info parsing and filename matching.
  HRIT and HRPT l1b filepatterns are implemented. [Panu Lahtinen]

- Added a function that reads filepattern template xml for trollstalker.
  [Panu Lahtinen]

- Install etc/ directory. [Panu Lahtinen]

- Possibility to use configuration files. File info parsing based on xml
  template. [Panu Lahtinen]

- Moved to examples/ [Panu Lahtinen]

- Moved to examples. [Panu Lahtinen]

- Moved to examples. [Panu Lahtinen]

- Moved to examples/ [Panu Lahtinen]

- Adapted to new message format from trollstalker. [Panu Lahtinen]

- Refactored zenith angle and satellite checks to methods, minor
  cleanup. [Panu Lahtinen]

- Added comment on Sun zenith angle limits. [Panu Lahtinen]

- Sun zenith angle limitations relative to image center. [Panu Lahtinen]

- Step-by-step instructions. [Panu Lahtinen]

- Old stuff. [Panu Lahtinen]

- Old stuff. [Panu Lahtinen]

- Old stuff. [Panu Lahtinen]

- Fixed product_config_file tag. [Panu Lahtinen]

- Execution bit set. [Panu Lahtinen]

- Moved to trollduction/bin/ [Panu Lahtinen]

- Moved to trollduction/bin/ [Panu Lahtinen]

- Moved to trollduction/bin/ [Panu Lahtinen]

- Moved to trollduction/bin/ [Panu Lahtinen]

- Fixed imports, moved to bin/ [Panu Lahtinen]

- Fixed imports. [Panu Lahtinen]

- Sunzen tags renamed. [Panu Lahtinen]

- Imports fixed. [Panu Lahtinen]

- Fixed channel data load/unload. [Panu Lahtinen]

- More configuration items used. Also better channel load/unload
  function. [Panu Lahtinen]

- Delete unneeded files. [Panu Lahtinen]

- Working example config. [Panu Lahtinen]

- Couple of semantic changes. [Panu Lahtinen]

- XML reader/parser adapted for Trollduction. [Panu Lahtinen]

- Partly adapted to use configuration files. [Panu Lahtinen]

- Updated configuration file. [Panu Lahtinen]

- Typo. [Panu Lahtinen]

- First guess of product config file. [Panu Lahtinen]

- Typo. [Panu Lahtinen]

- Reorganize and plans for class member structuring. [Panu Lahtinen]

- Adjusted to use ListenerContainer class. [Panu Lahtinen]

- Container class added. [Panu Lahtinen]

- Grouped satellite information to dictionary, and removed duplicate
  time_slot parameter from draw_images. [Panu Lahtinen]

- Satellite information to Trollduction attributes. [Panu Lahtinen]

- Updated listener restart to new posttroll version. [Panu Lahtinen]

- Removed white space from listener inits. [Panu Lahtinen]

- Removed white spaces from file types. [Panu Lahtinen]

- File types changed and a small cleanup. [Panu Lahtinen]

- Merge branch 'feature_new_posttroll' into develop. [Martin Raspaud]

  Conflicts:
  	trollduction/trollduction.py


- Merge branch 'feature_new_posttroll' of
  github.com:mraspaud/trollduction into feature_new_posttroll. [Martin
  Raspaud]

- Working filemask. [Panu Lahtinen]

- Adapt to the new posttroll, and cleanup a few things. [Martin Raspaud]

- Merge branch 'develop' of https://github.com/mraspaud/trollduction
  into develop. [Panu Lahtinen]

- Change the copyright year... [Martin Raspaud]

- Minor fixes and updates to docstrings. [Panu Lahtinen]

- Member functions. [Panu Lahtinen]

- Added a line in the documentation. [Martin Raspaud]

- Added documentation template. [Martin Raspaud]

- Add support for travis, add the test framework structure. [Martin
  Raspaud]

- Merge branch 'master' into develop. [Martin Raspaud]

  Conflicts:
  	trollduction/listener.py

- Outdated parallel functions. [Panu Lahtinen]

- Main for testing without config file. [Panu Lahtinen]

- Main for testing without config file. [Panu Lahtinen]

- Testable version with serial processing. [Panu Lahtinen]

- Added fileinfo parsing to message. [Panu Lahtinen]

- Minor updates for better usability. [Panu Lahtinen]

- Main() for testing trollduction. [Panu Lahtinen]

- First runnable version. [Panu Lahtinen]

- Pyinotify with messaging for trollduction. [Panu Lahtinen]

- Example main for completed system. [Panu Lahtinen]

- Skeleton version of trollduction.py and a working listener.py. [Panu
  Lahtinen]

- Better handling of thread pool and some error handling. [Martin
  Raspaud]

   * semaphore is now acquired before thread creation
   * unknown format error doesn't crash thread
   * generate_composites now accepts hooks

- Remove relative imports and added a setup.py and version.py. [Martin
  Raspaud]

- Semaphore to avoid fork bombs. [Martin Raspaud]

- Add overlay dynamically. [Martin Raspaud]

- Changed orbit to orbit_number in messages. [Martin Raspaud]

- Merge branch 'develop' of github.com:mraspaud/trollduction into
  develop. [Martin Raspaud]

- Renamed dirstalker_sat.py to dirstalker.py. [karjaljo]

- Sample xml product list. [Martin Raspaud]

- WIP Producer. Creates images now :) [Martin Raspaud]

- Added a few more info items in dirstalker_sat.py and an example
  message. [Martin Raspaud]

- Adding the __init__.py file to make trollduction a package. [Martin
  Raspaud]

- Rename postroll_listener to producer.py. [Martin Raspaud]

- Merge branch 'develop' of https://github.com/mraspaud/trollduction
  into develop. [karjaljo]

- Added self.subscriber to class members. [Panu Lahtinen]

- Listener class and a simple publisher for testing. [Panu Lahtinen]

- Added logger configuration file and logger init function. [karjaljo]

- Initial code commit. [Martin Raspaud]

- Add ~ files to .gitignore. [Martin Raspaud]

- Initial commit. [Martin Raspaud]


