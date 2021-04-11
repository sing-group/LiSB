import json
import os.path
import logging
import logging.config
import time


def config_logging():
    path = '../logs/'
    if not os.path.exists(path):
        os.makedirs(path)

    with open('../conf/logging.json', 'r') as file:
        config = json.load(file)

    logging.config.dictConfig(config)


config_logging()

while True:
    logging.debug("Debug msg")
    logging.info("Info msg")
    logging.warning("Warning msg")
    logging.error("Error msg")
    time.sleep(5)
