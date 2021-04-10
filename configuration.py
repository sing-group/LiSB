import ipaddress
import json
import logging
import os
import re
import socket

from schema import Schema, And, Use, Optional, SchemaError, Or

from spamfilter.filtering import Filter, DBFilter

# ALL FILTER CLASSES
filter_classes = [cls.__name__ for cls in Filter.__subclasses__() if cls.__name__ != 'DBFilter']
filter_classes.extend(cls.__name__ for cls in DBFilter.__subclasses__())

# EMAIL REGEX
email_regex = re.compile('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$')

# SCHEMA FOR THE FILTERING CONFIGURATION
filtering_schema = Schema(
    {
        "disabled-filters": [And(str, lambda cls: cls in filter_classes)],
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
        "email-alerts": {
            "status": Or("enabled", "disabled"),
            "level": Or("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
            "msg-template": str
        }
    },
    ignore_extra_keys=True
)

# SCHEMA FOR THE COMMUNICATIONS CONFIGURATION
communications_schema = Schema(
    {
        "admin-emails": And(
            [And(str, lambda email: re.match(email_regex, email) is not None)],
            lambda admin_emails: admin_emails
        ),
        "server-email": And(str, lambda email: re.match(email_regex, email) is not None)
    }
)

# SCHEMA FOR THE SERVER PARAMETERS
# server_params_schema = Schema(
#     {
#         "n-filtering-threads": And(int, lambda n: n > 0),
#         "n-forwarder-threads": And(int, lambda n: n > 0),
#         "storing-frequency": And(int, lambda n: n > 0)
#     }
# )


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
    config_files = ["logging", "communications", "filtering", "server_params"]
    for filename in config_files:
        # Open configuration file
        with open("conf/" + filename + ".json") as file:
            conf[filename] = json.load(file)
        # Validate if necessary
        validation_schema: Schema = globals().get(filename + "_schema")
        if validation_schema is not None:
            validation_schema.validate(conf[filename])
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
        if logging_conf['email-alerts']['status'] == 'enabled':
            # Get all parameters
            email_alerts_level = logging_conf['email-alerts']['level']
            msg_template = logging_conf['email-alerts']['msg-template']
            server_email = server_conf['communications']['server-email']
            admin_emails = server_conf['communications']['admin-emails']

            # Set up email handler
            email_handler = logging.handlers.SMTPHandler(
                mailhost=server_conf['forwarding']['remote-addr'],
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

    except Exception:
        logging.basicConfig(
            filename='logs/log',
            format="[ %(asctime)s ] [ %(levelname)s ] [ %(module)s : %(threadName)s ] %(message)s",
            level=logging.WARNING
        )
        logging.error(f"There was a problem while setting up logging. Using basic configuration:"
                      f" - Storing logs in logs/"
                      f" - Logging level: WARNING"
                      f" - Using format [ %(asctime)s ] [ %(levelname)s ] [ %(module)s : %(threadName)s ] %(message)s")
