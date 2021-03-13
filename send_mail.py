import smtplib
import email.utils
import socket
from email.mime.text import MIMEText

# Create the message
msg = MIMEText('Hi Cesar! I hope you are doing great! When can we meet up? It\'s been so long. Love, Eliana')
msg['To'] = email.utils.formataddr(('Recipient', 'cmrodriguez17@example.com'))
msg['From'] = email.utils.formataddr(('Author', 'eacappello17@example.com'))
msg['Subject'] = 'Hi Cesar!'

# Get private IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server_ip = s.getsockname()[0]
s.close()
server = smtplib.SMTP(server_ip, 1025)
server.set_debuglevel(True)  # show communication with the server
try:
    print('\nSending message to (', server_ip, ':', 1025, ')')
    server.sendmail('spam@example.com', ['cmrodriguez17@example.com'], msg.as_string())
finally:
    server.quit()
