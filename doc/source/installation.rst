.. .. sectnum::
..   :depth: 4
..   :start: 1
..   :suffix: .

Installation
============

The easiest way to install trollduction with all the dependencies is
to use *pip*::

  $ pip install trollduction

or::

  $ pip install trollduction --user

You can download the trollduction source code from github_,::

  $ git clone https://github.com/pytroll/trollduction.git

and then run::

  $ cd trollduction
  $ python setup.py install

to install. If installing system-wide, command *sudo* needs to be added before
*python*, or login as user *root*. If you want to install locally on your user
account, you can run instead::

  $ python setup.py install --user

Trollduction is also available as a ZIP package from github_, when selecting the before mentioned branch and then from the right *Download ZIP* button.

.. _github: https://github.com/pytroll/trollduction


Prerequisities
--------------

If everything goes well, all the prerequisites for trollduction should be
installed automatically when installing trollduction. 

Here is however a list of some of the requirements for *trollduction*.

    * pytroll-collectors_ - data collecting and notifying of data availability
    * mpop_ - satellite data readers
    * mipp_ - readers for geostationary satellites
    * pyresample_ - data resampling
    * posttroll_ - messaging between modules
    * pyorbital_ - orbital calculations
    * trollsift_ - reverse .format() for parsing information from strings
    * trollduction_ - satellite data batch processing
    * pytroll-schedule_ - satellite overpass scheduling
    * pyspectral_ - spectral calculations for satellite data
    * pykdtree_ - K-d tree implementation for pyresample
    * python-geotiepoints_ - calculate swath coordinates for tiepoint data
    * trollimage_ - image handling functions
    * pycoast_ - add coastlines, graticules etc. shapes on images

.. _mpop: https://github.com/pytroll/mpop
.. _mipp: https://github.com/pytroll/mipp
.. _pyresample: https://github.com/pytroll/pyresample/
.. _posttroll: https://github.com/pytroll/posttroll
.. _pyorbital: https://github.com/pytroll/pyorbital
.. _trollsift: https://github.com/pytroll/trollsift
.. _trollduction: https://github.com/pytroll/trollduction
.. _pytroll-schedule: https://github.com/pytroll/pytroll-schedule
.. _pyspectral: https://github.com/pytroll/pyspectral
.. _pykdtree: https://github.com/storpipfugl/pykdtree
.. _python-geotiepoints: https://github.com/pytroll/python-geotiepoints
.. _trollimage: https://github.com/pytroll/trollimage
.. _pycoast: https://github.com/pytroll/pycoast 


