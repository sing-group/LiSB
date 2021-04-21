import asyncore
import logging

from schema import SchemaError

from spamfilter import SpamFilterServer, configuration

try:
    # Load initial configurations
    server_conf = configuration.load_server_config()
    configuration.config_logging(server_conf)
    # Launch SpamFilterServer
    SpamFilterServer(server_conf)
    asyncore.loop()
except SchemaError as e:
    logging.error(f"There was a syntax error in one of the configuration files:\n{e}")
except Exception as e:
    logging.error(f"An unexpected error occurred:\n\tError type: {e.__class__.__name__}\n\tDescription: {e}")
