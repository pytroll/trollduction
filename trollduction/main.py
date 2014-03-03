#!/usr/bin/python

import sys
import trollduction

if __name__ == '__main__':

    # Trollduction configuration file
    fname = sys.argv[1]
    # Create a new Trollduction instance, initialised with the config
    td = trollduction.Trollduction(fname)
    # Run Trollduction
    td.run_single()

