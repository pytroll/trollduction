#!/usr/bin/env python

"""Main script for trollflow based trollduction"""

import logging
import logging.config
import yaml
import sys
import time

from trollflow.workflow_launcher import WorkflowStreamer

def generate_daemon(config_item):
    return config_item['components'][-1]['class']

def generate_workflow(config_item):
    wfs = WorkflowStreamer(config=config_item)
    wfs.start()
    return wfs

TYPES = {'daemon': generate_daemon,
         'workflow': generate_workflow}

def main():
    """Main()"""

    # Read config
    with open(sys.argv[1], "r") as fid:
        config = yaml.load(fid)

    # Check if log config is available, use it if it is
    for item in config["config"]:
        if "log_config" in item.keys():
            logging.config.fileConfig(item["log_config"],
                                      disable_existing_loggers=False)

    logger = logging.getLogger("flow_processor")
    logger.info("Initializing pluginized Trollduction")

    workers = []

    for item in config['work']:
        workers.append(TYPES[item['type']](item))

    queue = None
    for worker in workers:
        if queue is not None:
            worker.input_queue = queue
        queue = worker.output_queue

    logger.info("Ready to process new scenes")

    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Closing flow processing items")
            for worker in workers:
                worker.stop()
                try:
                    worker.input_queue.join()
                except AttributeError:
                    pass
                try:
                    worker.output_queue.join()
                except AttributeError:
                    pass
            break

    logger.info("Trollduction has been shutdown.")

if __name__ == "__main__":
    main()
