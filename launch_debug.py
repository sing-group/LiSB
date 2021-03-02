import smtpd
import asyncore
import socket

server_ip = socket.gethostbyname(socket.gethostname())
server_ip = '192.168.1.188'
server = smtpd.DebuggingServer(('192.168.1.188', 1025), None)
print("Running SMTP Debug Server on ", server_ip)
print("Waiting for emails...")

asyncore.loop()
