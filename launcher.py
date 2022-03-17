#!/var/www/lisb/venv/bin/python
import logging
from schema import SchemaError

from core import configuration
from core.LiSBServer import LiSBServer

if __name__ == '__main__':

    try:
        # Load initial configurations
        server_conf = configuration.load_server_config()
        configuration.config_logging(server_conf)
        # Launch LiSBServer
        server = LiSBServer(server_conf)
        server.launch_server()
    except SchemaError as e:
        logging.error(f"There was a syntax error in one of the configuration files: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e.__class__.__name__} - {e}")
