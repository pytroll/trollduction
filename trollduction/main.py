#!/usr/bin/python

import sys
from trollduction import Trollduction

if __name__ == '__main__':

    # Trollduction configuration file
    td_config = sys.argv[1]
    # Create a new Trollduction instance, initialised with the config
    td = Trollduction(td_config=td_config)
    # Run Trollduction
    td.run()

