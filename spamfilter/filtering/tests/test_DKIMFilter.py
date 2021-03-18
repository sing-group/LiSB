import email
from unittest import TestCase

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter
from spamfilter.filtering.filters.DKIMFilter import DKIMFilter


class TestDKIMFilter(TestCase):
    tested_filter = DKIMFilter()

    def test_valid_1(self):
        file = open("msgs/test_email_msg.eml")
        msg = email.message_from_file(file)
        envelope = EmailEnvelope(
            peer='192.168.1.2',
            mail_from=Filter.parse_from_and_to(msg.get('From')),
            rcpt_tos=[Filter.parse_from_and_to(to_parse) for to_parse in msg.get("To").split(",")],
            email_msg=msg
        )
        self.tested_filter.set_initial_data({})
        is_spam = self.tested_filter.filter(envelope)
        self.assertFalse(is_spam, "DKIMFilter detected ham as spam")

    def test_valid_2(self):
        file = open("msgs/test_email_msg.eml")
        msg = email.message_from_file(file)
        envelope = EmailEnvelope(
            peer='192.168.1.2',
            mail_from=Filter.parse_from_and_to(msg.get('From')),
            rcpt_tos=[Filter.parse_from_and_to(to_parse) for to_parse in msg.get("To").split(",")],
            email_msg=msg
        )
        dkim = DKIMFilter.get_dkim_params(msg)
        self.tested_filter.set_initial_data(
            {
                Filter.get_domain(envelope.mail_from): {
                    's': dkim['s'],
                    'd': dkim['d']
                }
            }
        )
        is_spam = self.tested_filter.filter(envelope)
        self.assertFalse(is_spam, "DKIMFilter detected ham as spam")

    def test_spam_1(self):
        file = open("msgs/test_email_msg.eml")
        msg = email.message_from_file(file)
        envelope = EmailEnvelope(
            peer='192.168.1.2',
            mail_from=Filter.parse_from_and_to(msg.get('From')),
            rcpt_tos=[Filter.parse_from_and_to(to_parse) for to_parse in msg.get("To").split(",")],
            email_msg=msg
        )
        dkim = DKIMFilter.get_dkim_params(msg)
        self.tested_filter.set_initial_data(
            {
                Filter.get_domain(envelope.mail_from): {
                    's': 'other_s',
                    'd': 'other_d'
                }
            }
        )
        is_spam = self.tested_filter.filter(envelope)
        self.assertTrue(is_spam, "DKIMFilter detected ham as spam")