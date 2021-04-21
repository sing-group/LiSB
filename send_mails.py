import random
import smtplib
import email
import socket
import threading
import time
from email.mime.text import MIMEText
from spamfilter.filtering.tests.test_AnyFilter import TestAnyFilter


def msg1():
    # Create the message
    msg = MIMEText('Hi Cesar! I hope you are doing great! When can we meet up? It\'s been so long. Love, Eliana')
    msg['To'] = email.utils.formataddr(('Recipient', 'cmrodriguez17@example.com'))
    msg['From'] = email.utils.formataddr(('Author', 'eacappello17@example.com'))
    msg['Return-Path'] = 'cmrodriguez17@example.com'
    msg['Subject'] = 'Hi Cesar!'
    return msg


def msg2():
    with open("spamfilter/filtering/tests/msgs/test_email_msg.eml") as file:
        return email.message_from_file(file)


def send_mail(ip, port, email_msg):
    server = smtplib.SMTP(ip, port)
    # server.set_debuglevel(True)  # show communication with the server
    try:
        print(f'\nSending message to ({ip}:1025)')
        time.sleep(random.randrange(0,3))
        parsed_from = TestAnyFilter.parse_from_and_to(email_msg.get('From'))
        parsed_tos = [TestAnyFilter.parse_from_and_to(to_parse) for to_parse in email_msg.get("To").split(",")]
        server.sendmail(parsed_from, parsed_tos, email_msg.as_string())
    except Exception as e:
        print(e)
    finally:
        server.quit()


# Create msg
msg = msg2()

# Get private IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server_ip = s.getsockname()[0]
s.close()

# Get port
server_port = 1025

# Launch threads
n_sending_threads = 1
for thread_index in range(n_sending_threads):
    worker = threading.Thread(
        target=send_mail,
        name=f"SendingThread-{thread_index}",
        args=(server_ip, server_port, msg)
    )
    worker.start()
