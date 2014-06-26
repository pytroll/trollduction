.. .. sectnum::
..   :depth: 4
..   :start: 1
..   :suffix: .

Installation
============

Prerequisities
--------------

You need to have the following packages, and their requirements, installed before installing *trollduction*.

* mpop_ - select *pre-master* branch
* pyresample_
* posttroll_ - select *feature_service* branch
* pyorbital_
* trollsift_
* python-lxml
* python-pyinotify

.. _mpop: https://github.com/mraspaud/mpop
.. _pyresample: https://code.google.com/p/pyresample/
.. _posttroll: https://github.com/mraspaud/posttroll
.. _pyorbital: https://github.com/mraspaud/pyorbital
.. _trollsift: https://github.com/pnuu/trollsift

Trollduction
------------

You can download the trollduction source code from github_,::

  $ git clone -b develop https://github.com/mraspaud/trollduction.git

and then run::

  $ cd trollduction
  $ python setup.py install

to install. If installing system-wide, command *sudo* needs to be added before *python*, or login as user *root*.

Trollduction is also available as a ZIP package from github_, when selecting the aforementioned branch and then from the right *Download ZIP* button.

.. _github: https://github.com/mraspaud/trollduction
