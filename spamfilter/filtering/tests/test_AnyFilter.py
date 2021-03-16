import email
import importlib
from email.mime.text import MIMEText
from os import listdir
from os.path import isfile, join
import socket
from typing import Sequence
from unittest import TestCase

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter
from spamfilter.filtering.tests.EmailWithFile import EmailWithFile


class TestAnyFilter(TestCase):
    valid_emails: Sequence[EmailWithFile]
    tested_filter: Filter
    this_ip: str

    def __init__(self, *args, **kwargs):

        # Call parent constructor
        super(TestAnyFilter, self).__init__(*args, **kwargs)

        # Create Filter object to be tested
        class_name = type(self).__name__
        if class_name != "TestAnyFilter":
            to_be_tested = class_name[4:len(class_name)]
            module = importlib.import_module("spamfilter.filtering.filters." + to_be_tested)
            filter_class = getattr(module, to_be_tested)
            self.tested_filter = filter_class()

        # Get this PC's IP address. It will be used as the peer address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.this_ip = s.getsockname()[0]
        s.close()

        # Load all valid mails to be tested in the filter
        path = "./valid_msgs"
        all_file_names = [f for f in listdir(path) if isfile(join(path, f))]
        self.valid_emails = list()
        for file_name in all_file_names:
            # Read and parse email
            file = open(join(path, file_name), "r")
            msg_data = email.message_from_file(file)
            msg = EmailEnvelope(self.this_ip, msg_data.get("From"), [msg_data.get("To")], msg_data)
            # Append to list with file
            ewf = EmailWithFile(file_name, msg)
            self.valid_emails.append(ewf)

    def test_valid_emails(self):
        if type(self) == TestAnyFilter:
            self.assertTrue(True)
        else:
            for ewf in self.valid_emails:
                is_spam = self.tested_filter.filter(ewf.msg)
                self.assertFalse(is_spam, msg=f"Email '{ewf.file_name}' was detected as spam but it is not")

    def test_valid_1(self):
        if type(self) == TestAnyFilter:
            self.assertTrue(True)
        else:
            valid = self.create_email(
                peer=self.this_ip,
                mail_from="from@mail.com",
                rcpt_tos=["to1@mail.com", "to2@mail.com"],
                email_from=("Author", "from@mail.com"),
                email_tos=[("Recipient1", "to1@mail.com"), ("Recipient2", "to2@mail.com")],
                email_subject="Valid",
                email_contents="This is a valid mail for testing purposes"
            )
            print("TESTING VALID 1:\n", valid)
            not_spam = self.tested_filter.filter(valid)
            self.assertFalse(not_spam, "Filter detected spam incorrectly")

    def test_valid_2(self):
        if type(self) == TestAnyFilter:
            self.assertTrue(True)
        else:
            valid = self.create_email(
                peer=self.this_ip,
                mail_from="from@mail.com",
                rcpt_tos=["to@mail.com"],
                email_from=("Author", "from@mail.com"),
                email_tos=[("Recipient", "to@mail.com")],
                email_subject="Valid",
                email_contents="This is a valid mail for testing purposes"
            )
            print("TESTING VALID 2:\n", valid)
            not_spam = self.tested_filter.filter(valid)
            self.assertFalse(not_spam, "Filter detected spam incorrectly")

    @staticmethod
    def create_email(peer, mail_from, rcpt_tos, email_from, email_tos, email_subject, email_contents) -> EmailEnvelope:
        # Create the message
        msg = MIMEText(email_contents)
        msg['To'] = ", ".join([email.utils.formataddr(to) for to in email_tos])
        msg['From'] = email.utils.formataddr(email_from)
        msg['Subject'] = email_subject

        # Create and return the envelope
        envelope = EmailEnvelope(peer, mail_from, rcpt_tos, msg)
        return envelope
