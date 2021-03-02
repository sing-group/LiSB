import asyncore
import socket
import spamfilter as sf

server_ip = socket.gethostbyname(socket.gethostname())
server_ip = '192.168.1.156'
server = sf.SpamFilter((server_ip, 1025), ('192.168.1.188', 1025), None)
print("Running SpamFilter on ", server_ip)
print("Waiting for mails to filter...")

asyncore.loop()
