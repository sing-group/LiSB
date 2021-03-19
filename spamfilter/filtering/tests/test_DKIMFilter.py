import email
from unittest import TestCase

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter
from spamfilter.filtering.filters.DKIMFilter import DKIMFilter
from spamfilter.filtering.tests.test_AnyFilter import TestAnyFilter


class TestDKIMFilter(TestAnyFilter):
    tested_filter = DKIMFilter()

    def test_valid_1(self):
        file = open("msgs/test_email_msg.eml")
        msg = email.message_from_file(file)
        envelope = EmailEnvelope(
            peer='192.168.1.2',
            mail_from=TestAnyFilter.parse_from_and_to(msg.get('From')),
            rcpt_tos=[TestAnyFilter.parse_from_and_to(to_parse) for to_parse in msg.get("To").split(",")],
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
            mail_from=TestAnyFilter.parse_from_and_to(msg.get('From')),
            rcpt_tos=[TestAnyFilter.parse_from_and_to(to_parse) for to_parse in msg.get("To").split(",")],
            email_msg=msg
        )
        dkim = envelope.get_dkim_params()
        self.tested_filter.set_initial_data(
            {
                envelope.get_sender_domain(): {
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
            mail_from=TestAnyFilter.parse_from_and_to(msg.get('From')),
            rcpt_tos=[TestAnyFilter.parse_from_and_to(to_parse) for to_parse in msg.get("To").split(",")],
            email_msg=msg
        )
        dkim = envelope.get_dkim_params()
        self.tested_filter.set_initial_data(
            {
                envelope.get_sender_domain(): {
                    's': 'other_s',
                    'd': 'other_d'
                }
            }
        )
        is_spam = self.tested_filter.filter(envelope)
        self.assertTrue(is_spam, "DKIMFilter detected ham as spam")