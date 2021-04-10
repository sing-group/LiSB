import asyncore

import configuration
from spamfilter import SpamFilter

# Looad initial configurations
server_conf = configuration.load_server_config()
configuration.config_logging(server_conf)

# Get launching params
server_ip = configuration.get_local_ip()
server_port = server_conf["server_params"]["local_port"]
remote_ip = server_conf["server_params"]["remote_ip"]
remote_port = server_conf["server_params"]["remote_ip"]

# Launch SpamFilter
SpamFilter(
    (server_ip, server_port),
    (remote_ip, remote_port),
    None
)
asyncore.loop()
