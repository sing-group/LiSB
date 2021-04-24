import ipaddress
import json
import logging
import os
import re
import socket
from os import listdir

from schema import Schema, And, Or

from spamfilter.filtering import Filter, DBFilter

# ALL FILTER CLASSES
filter_classes = [cls.__name__ for cls in Filter.__subclasses__() if cls.__name__ != 'DBFilter']
filter_classes.extend(cls.__name__ for cls in DBFilter.__subclasses__())

# EMAIL REGEX
email_regex = re.compile('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$')

# SCHEMA FOR THE FILTERING CONFIGURATION
filtering_schema = Schema(
    {
        "enable_threading": bool,
        "storing_frequency": And(int, lambda n: n > 0),
        "black_listing_threshold": And(int, lambda n: n > 0),
        "black_listed_days": And(int, lambda n: n > 0),
        "time_limit": And(float, lambda n: n > 0),
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

# SCHEMA FOR THE EMAIL ALERTS CONFIGURATION
logging_schema = Schema(
    {
        "email_alerts": {
            "status": Or("enabled", "disabled"),
            "level": Or("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
            "msg_template": str
        }
    },
    ignore_extra_keys=True
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
        "data_size_limit": And(int, lambda n: n > 0),
        "map": And(lambda obj: obj is None or isinstance(obj, dict)),
        "enable_SMTPUTF8": bool,
        "decode_data": bool
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
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


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
        validation_schema: Schema = globals().get(filename + "_schema")
        if validation_schema is not None:
            validated = validation_schema.validate(conf[filename])
            if not validation_schema.ignore_extra_keys:
                conf[filename] = validated

    return conf


def config_logging(server_conf: dict):
    """
    This function configures logging using the configuration stored in the conf/logging.json file.
    If any problem is encountered while setting up logging, then it defines a basic logging configuration.
    """
    # Create logging directory if it doesn't exist
    path = 'logs/'
    if not os.path.exists(path):
        os.makedirs(path)

    logging_conf = server_conf.get('logging')

    try:
        # Configure logging from file
        logging.config.dictConfig(logging_conf)

        # If email alerts are configured, then create email handler and configure it to send emails to admins
        if logging_conf['email_alerts']['status'] == 'enabled':
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
                subject=f"SpamFilter server alert",
                secure=None,
                credentials=None
            )
            email_handler.setLevel(email_alerts_level)
            email_formatter = logging.Formatter(msg_template)
            email_handler.setFormatter(email_formatter)
            logger = logging.getLogger()
            logger.addHandler(email_handler)

    except Exception as e:
        logging.basicConfig(
            filename='logs/log',
            format="[ %(asctime)s ] [ %(levelname)s ] [ %(module)s : %(threadName)s ] %(message)s",
            level=logging.WARNING
        )
        logging.error(f"There was a problem while setting up logging. Using basic configuration:\n"
                      f" - Storing logs in logs/\n"
                      f" - Logging level: WARNING\n"
                      f" - Using format [ %(asctime)s ] [ %(levelname)s ] [ %(module)s : %(threadName)s ] %(message)s\n"
                      f"PROBLEM: {e}")
