import smtplib
import email.utils
import socket
from email.mime.text import MIMEText

# Create the message
msg = MIMEText('This is the body of the message.')
msg['To'] = email.utils.formataddr(('Recipient', 'recipient@example.com'))
msg['From'] = email.utils.formataddr(('Author', 'author@example.com'))
msg['Subject'] = 'Simple test message'

server_ip = socket.gethostbyname(socket.gethostname())
server_ip = '192.168.1.156'
server = smtplib.SMTP(server_ip, 1025)
server.set_debuglevel(True)  # show communication with the server
try:
    print('Sending test email from ', server_ip)
    server.sendmail('author@example.com', ['recipient@example.com'], msg.as_string())
finally:
    server.quit()
