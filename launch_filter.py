import asyncore
import socket
import spamfilter as sf

# Get private IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server_ip = s.getsockname()[0]
s.close()

# Launch SpamFilter
source_port = dest_port = 1025
server = sf.SpamFilter((server_ip, source_port), ('172.20.10.12', dest_port), None)

asyncore.loop()
