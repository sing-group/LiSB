import smtpd
import asyncore
import socket

# server_ip = socket.gethostbyname(socket.gethostname())
server_ip = '192.168.1.188'
port = 1025
server = smtpd.DebuggingServer((server_ip, port), None)
print(f"Running SMTP Debug Server on destination: ({server_ip}:{port})")
print("Waiting for emails...")

asyncore.loop()
