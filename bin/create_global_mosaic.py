#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import yaml
import logging
import logging.handlers

from trollduction.global_mosaic import WorldCompositeDaemon


def main():
    """main()"""

    with open(sys.argv[1], "r") as fid:
        config = yaml.load(fid)

    try:
        if config["use_utc"]:
            os.environ["TZ"] = "UTC"
            time.tzset()
    except KeyError:
        pass

    # TODO: move log config to config file

    handlers = []
    handlers.append(
        logging.handlers.TimedRotatingFileHandler(config["log_fname"],
                                                  "midnight",
                                                  backupCount=21))

    handlers.append(logging.StreamHandler())

    try:
        loglevel = getattr(logging, config["log_level"])
    except KeyError:
        loglevel = logging.INFO

    for handler in handlers:
        handler.setFormatter(logging.Formatter("[%(levelname)s: %(asctime)s :"
                                               " %(name)s] %(message)s",
                                               '%Y-%m-%d %H:%M:%S'))
        handler.setLevel(loglevel)
        logging.getLogger('').setLevel(loglevel)
        logging.getLogger('').addHandler(handler)

    logger = logging.getLogger("WorldComposite")

    # Create and start compositor
    compositor = WorldCompositeDaemon(config)
    compositor.set_logger(logger)
    compositor.run()


if __name__ == "__main__":
    main()
