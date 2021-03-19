import smtplib
import email
import socket
from email.mime.text import MIMEText

# Create the message
# msg = MIMEText('Hi Cesar! I hope you are doing great! When can we meet up? It\'s been so long. Love, Eliana')
# msg['To'] = email.utils.formataddr(('Recipient', 'cmrodriguez17@example.com'))
# msg['From'] = email.utils.formataddr(('Author', 'eacappello17@example.com'))
# msg['Return-Path'] = 'cmrodriguez17@example.com'
# msg['Subject'] = 'Hi Cesar!'
from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.tests.test_AnyFilter import TestAnyFilter

file = open("spamfilter/filtering/tests/msgs/test_email_msg.eml")
msg = email.message_from_file(file)
file.close()

# Get private IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server_ip = s.getsockname()[0]
s.close()

server = smtplib.SMTP(server_ip, 1025)
server.set_debuglevel(True)  # show communication with the server
try:
    print(f'\nSending message to ({server_ip}:1025)')
    parsed_from = TestAnyFilter.parse_from_and_to(msg.get('From'))
    parsed_tos = [TestAnyFilter.parse_from_and_to(to_parse) for to_parse in msg.get("To").split(",")]
    server.sendmail(parsed_from, parsed_tos, msg.as_string())
finally:
    server.quit()
