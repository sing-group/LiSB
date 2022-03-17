import ipaddress
import json
import logging
import logging.config
import logging.handlers
import os
import re
import socket
import time
from os import listdir
from smtplib import SMTP

from schema import Schema, And, Or

from core.filtering import Filter, PastFilter

# ALL FILTER CLASSES
filter_classes = [cls.__name__ for cls in Filter.__subclasses__() if cls.__name__ != 'PastFilter']
filter_classes.extend(cls.__name__ for cls in PastFilter.__subclasses__())

# EMAIL REGEX
email_regex = re.compile('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$')

# SCHEMA FOR THE FILTERING CONFIGURATION
filtering_schema = Schema(
    {
        "enable_threading": bool,
        "storing_frequency": And(int, lambda n: n > 0),
        "black_listing_threshold": And(int, lambda n: n > 0),
        "black_listed_days": And(int, lambda n: n > 0),
        "time_limit": And(Or(float, int), lambda n: n > 0),
        "disabled_filters": [And(str, lambda cls: cls in filter_classes)],
        "exceptions": {
            "ip_addresses": [
                And(str, lambda ip: ipaddress.IPv4Address(ip))
            ],
            "email_addresses": [
                And(str, lambda email: re.match(email_regex, email) is not None)
            ],
            "email_domains": [
                And(str, lambda domain: re.match('^(\w|\_|\-|\.)+[.]\w{2,3}$', domain) is not None)
            ]
        }
    }
)

# LOGGING SCHEMA
logging_schema = Schema(
    {
        "console_level": Or("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        "rotating_file": {
            "when": Or("S", "M", "H", "D", "W0", "W1", "W2", "W3", "W4", "W5", "W6", "midnight"),
            "interval": And(int, lambda interval: interval > 0),
            "level": Or("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
        },
        "email_alerts": {
            "status": Or("enabled", "disabled"),
            "level": Or("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
            "msg_template": str
        }
    }
)

# SCHEMA FOR THE COMMUNICATIONS CONFIGURATION
communications_schema = Schema(
    {
        "admin_emails": And(
            [And(str, lambda email: re.match(email_regex, email) is not None)],
            lambda admin_emails: admin_emails
        ),
        "server_email": And(str, lambda email: re.match(email_regex, email) is not None)
    }
)

# SCHEMA FOR THE SERVER PARAMETERS
server_params_schema = Schema(
    {
        "local_ip": And(str, lambda ip: ipaddress.IPv4Address(ip)),
        "local_port": And(int, lambda port: 0 <= port <= 65353),
        "SMTP_parameters": dict
    }
)

# FORWARDING SCHEMA
forwarding_schema = Schema(
    {
        "remote_ip": And(str, lambda ip: ipaddress.IPv4Address(ip)),
        "remote_port": And(int, lambda port: 0 <= port <= 65353),
        "n_forwarder_threads": And(int, lambda n: n > 0)
    }
)


def get_local_ip():
    """
    This function can be used to find the private IP address of the current device.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def get_config_schema(filename) -> Schema:
    """
    This function is used in order to get the respective validation schema of a given file
    :param filename: the name of the file to get validation schema for
    """
    return globals().get(filename + "_schema")


def load_server_config():
    """
    This function loads and (validates if necessary) all of the server configurations located in the 'conf/' directory into the configuration dictionary
    """
    conf = {}
    config_files = [file[:-5] for file in listdir("conf/")]
    minimum_config_files = ["logging", "communications", "filtering", "server_params", "forwarding"]
    if set(minimum_config_files) > set(config_files):
        raise Exception("One or more minimum configuration files are missing. Please ensure that all of"
                        f"the following files are in the conf/ directory: {minimum_config_files}")
    for filename in config_files:
        # Open configuration file
        with open("conf/" + filename + ".json") as file:
            conf[filename] = json.load(file)
        # Validate if necessary
        validation_schema = get_config_schema(filename)
        if validation_schema is not None:
            validated = validation_schema.validate(conf[filename])
            if not validation_schema.ignore_extra_keys:
                conf[filename] = validated

    return conf


class UTCFormatter(logging.Formatter):
    """
    This class is used in order to format the logging timestamp to UTC time
    """
    converter = time.gmtime


# DEFAULT LOGGING CONFIGURATION
default_logging_conf = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "[ %(asctime)s ] [ %(levelname)s ] [ %(module)s : %(threadName)s ] %(message)s",
            "()": UTCFormatter
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "default",
            "filename": "logs/log",
            "when": "s",
            "interval": 10,
            "level": "INFO"
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": [
            "console",
            "file"
        ]
    },
    "email_alerts": {
        "status": "enabled",
        "level": "WARNING",
        "msg_template": "A new alert has been generated at %(asctime)s by %(module)s : %(message)s"
    }
}


def config_logging(server_conf: dict):
    """
    This function configures logging using the configuration stored in the conf/logging.json file.
    """
    # Create logging directory if it doesn't exist
    path = 'logs/'
    if not os.path.exists(path):
        os.makedirs(path)

    # Configure logging from file
    logging_conf = server_conf.get('logging')
    default_logging_conf['handlers']['console']['level'] = logging_conf['console_level']
    default_logging_conf['handlers']['file']['when'] = logging_conf['rotating_file']['when']
    default_logging_conf['handlers']['file']['interval'] = logging_conf['rotating_file']['interval']
    default_logging_conf['handlers']['file']['level'] = logging_conf['rotating_file']['level']
    logging.config.dictConfig(default_logging_conf)

    # If email alerts are configured, then create email handler and configure it to send emails to admins
    if logging_conf['email_alerts']['status'] == 'enabled':

        # Try to connect to the remote SMTP server.
        # If it is not possible, an exception will be raised
        try:
            # Connect to server
            connection = SMTP(server_conf['forwarding']['remote_ip'], server_conf['forwarding']['remote_port'])

            # Get all parameters
            email_alerts_level = logging_conf['email_alerts']['level']
            msg_template = logging_conf['email_alerts']['msg_template']
            server_email = server_conf['communications']['server_email']
            admin_emails = server_conf['communications']['admin_emails']

            # Set up email handler
            email_handler = logging.handlers.SMTPHandler(
                mailhost=(server_conf['forwarding']['remote_ip'], server_conf['forwarding']['remote_port']),
                fromaddr=server_email,
                toaddrs=admin_emails,
                subject=f"LiSB server alert",
                secure=None,
                credentials=None
            )
            email_handler.setLevel(email_alerts_level)
            email_formatter = logging.Formatter(msg_template)
            email_handler.setFormatter(email_formatter)
            logger = logging.getLogger()
            logger.addHandler(email_handler)

            # Close connection
            connection.close()
        except Exception as e:
            logging.error(f"There was a problem while setting up the email handler for logging: {e}")
