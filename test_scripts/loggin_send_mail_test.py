import smtplib

sender = 'no_reply@mydomain.com'
receivers = ['cmrodriguez17@esei.uvigo.es']

message = """From: No Reply <no_reply@mydomain.com>
To: Cesar <cmrodriguez17@esei.uvigo.es>
Subject: Test Email

This is a test e-mail message.
"""

try:
    smtpObj = smtplib.SMTP('192.168.1.156', 1025)
    smtpObj.sendmail(sender, receivers, message)
    print("Successfully sent email")
except smtplib.SMTPException as e:
    print(f"Error: unable to send email: {e}")
