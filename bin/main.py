#!/usr/bin/python

import sys
from trollduction.trollduction import Trollduction

if __name__ == '__main__':

    # Trollduction configuration file
    fname = sys.argv[1]
    # Create a new Trollduction instance, initialised with the config
    td = Trollduction(fname)
    # Run Trollduction
    td.run_single()

