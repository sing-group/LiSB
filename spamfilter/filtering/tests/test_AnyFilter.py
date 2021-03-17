import email
import importlib
from email.mime.text import MIMEText
from os import listdir
from os.path import isfile, join
import socket
from typing import Sequence
from unittest import TestCase

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.Filter import Filter
from spamfilter.filtering.tests.EmailWithFile import EmailWithFile


class TestAnyFilter(TestCase):
    valid_emails: Sequence[EmailWithFile]
    invalid_emails: Sequence[EmailWithFile]
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

        # Load all mails to be tested in the filter
        self.valid_emails = self.load_mails("./valid_msgs")
        self.invalid_emails = self.load_mails("./invalid_msgs")

    def load_mails(self, path):
        all_file_names = [f for f in listdir(path) if isfile(join(path, f))]
        emails = list()
        try:
            for file_name in all_file_names:
                # Read and parse email
                file = open(join(path, file_name), "r")
                msg_data = email.message_from_file(file)
                env_from = Filter.parse_from_and_to(msg_data.get('From'))
                if msg_data.get('To') is not None:
                    env_tos = [Filter.parse_from_and_to(to_parse) for to_parse in msg_data.get("To").split(",")]
                else:
                    env_tos = ['to@email.com']
                    msg_data.set_param('To', 'to@email.com')
                envelope = EmailEnvelope(self.this_ip, env_from, env_tos, msg_data)
                # Append to list with file
                ewf = EmailWithFile(file_name, envelope)
                emails.append(ewf)
        except Exception as e:
            print(f"Problem while parsing email '{file_name}': {e}")
        return emails

    def test_valid_emails(self):
        if type(self) == TestAnyFilter:
            self.assertTrue(True)
        else:
            spam = []

            try:
                for ewf in self.valid_emails:
                    is_spam = self.tested_filter.filter(ewf.msg)
                    if is_spam:
                        spam.append(ewf.file_name)
            except Exception as e:
                print(f"Error when processing file '{ewf.file_name}': {e}")

            print(f"Percentage of HAM properly detected: {(1 - len(spam) / len(self.valid_emails)) * 100}% ")
            print(f"Detected as HAM: {len(self.valid_emails) - len(spam)} ")
            print(f"Detected as SPAM: {len(spam)} ")
            self.assertTrue(not spam, msg="The following HAM emails were detected as spam:\n" + "\n".join(spam))

    def test_invalid_emails(self):
        if type(self) == TestAnyFilter:
            self.assertTrue(True)
        else:

            ham = []

            try:
                for ewf in self.invalid_emails:
                    is_spam = self.tested_filter.filter(ewf.msg)
                    if not is_spam:
                        ham.append(ewf.file_name)
            except Exception as e:
                print(f"Error when processing file '{ewf.file_name}': {e}")

            print(f"Percentage of SPAM properly detected: {(1 - len(ham) / len(self.invalid_emails)) * 100}% ")
            print(f"Detected as SPAM: {len(self.invalid_emails) - len(ham)} ")
            print(f"Detected as HAM: {len(ham)} ")
            self.assertTrue(not ham, msg="The following SPAM emails were detected as HAM:\n" + "\n".join(ham))

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
                email_contents="This is a valid mail for testing purposes",
                other_headers={
                    'Return-Path': 'from@mail.com'
                }
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
                email_contents="This is a valid mail for testing purposes",
                other_headers={
                    'Return-Path': 'to@mail.com'
                }
            )
            print("TESTING VALID 2:\n", valid)
            not_spam = self.tested_filter.filter(valid)
            self.assertFalse(not_spam, "Filter detected spam incorrectly")

    @staticmethod
    def create_email(peer, mail_from, rcpt_tos, email_from, email_tos, email_subject, email_contents,
                     other_headers={}) -> EmailEnvelope:
        # Create the message
        msg = MIMEText(email_contents)
        msg['To'] = ", ".join([email.utils.formataddr(to) for to in email_tos])
        msg['From'] = email.utils.formataddr(email_from)
        msg['Subject'] = email_subject
        for header in other_headers:
            msg[header] = other_headers[header]

        # Create and return the envelope
        envelope = EmailEnvelope(peer, mail_from, rcpt_tos, msg)
        return envelope
