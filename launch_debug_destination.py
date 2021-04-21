import smtpd
import asyncore
import socket

# Get private IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server_ip = s.getsockname()[0]
s.close()

# Configure port
port = 1025

# Launch DebuggingServer
server = smtpd.DebuggingServer((server_ip, port), None)
print(f"Running SMTP Debug Server on destination: ({server_ip}:{port})")
print("Waiting for emails...")
asyncore.loop()
