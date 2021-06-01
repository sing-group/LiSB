#!/etc/spamfilter/venv/bin/python3.8

import logging
from schema import SchemaError

from core import configuration
from core.SpamFilterServer import SpamFilterServer

if __name__ == '__main__':

    try:
        # Load initial configurations
        server_conf = configuration.load_server_config()
        configuration.config_logging(server_conf)
        # Launch SpamFilterServer
        server = SpamFilterServer(server_conf)
        server.launch_server()
    except SchemaError as e:
        logging.error(f"There was a syntax error in one of the configuration files:\n{e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred:\n\tError type: {e.__class__.__name__}\n\tDescription: {e}")
