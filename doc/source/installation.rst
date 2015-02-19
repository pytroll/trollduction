.. .. sectnum::
..   :depth: 4
..   :start: 1
..   :suffix: .

Installation
============

You can download the trollduction source code from github_,::

  $ git clone https://github.com/mraspaud/trollduction.git

and then run::

  $ cd trollduction
  $ python setup.py install

to install. If installing system-wide, command *sudo* needs to be added before
*python*, or login as user *root*. If you want to install locally on your user
account, you can run instead::

  $ python setup.py install --user

Trollduction is also available as a ZIP package from github_, when selecting the aforementioned branch and then from the right *Download ZIP* button.

.. _github: https://github.com/mraspaud/trollduction


Prerequisities
--------------

If everything goes well, all the prerequisites for trollduction should be
installed automatically when installing trollduction. 

Here is however a list of some of the requirements for *trollduction*.

* mpop_ - select *pre-master* branch
* pyresample_
* posttroll_ - select *develop* branch
* pyorbital_
* trollsift_
* python-pyinotify
* trollduction_ - select *feature-aapp-and-npp* branch
* pytroll-schedule_ - select *develop* branch

.. _mpop: https://github.com/mraspaud/mpop
.. _pyresample: https://code.google.com/p/pyresample/
.. _posttroll: https://github.com/mraspaud/posttroll
.. _pyorbital: https://github.com/mraspaud/pyorbital
.. _pytroll-schedule: https://github.com/mraspaud/pytroll-schedule
.. _trollsift: https://github.com/pnuu/trollsift
.. _trollduction: https://github.com/mraspaud/trollduction


