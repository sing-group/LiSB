import email
from unittest import TestCase

from core.EmailEnvelope import EmailEnvelope
from core.filtering.filters.SPFFilter import SPFFilter
from core.filtering.tests.test_AnyFilter import TestAnyFilter


class TestSPFFilter(TestCase):
    tested_filter = SPFFilter()

    def test_valid_1(self):
        envelope = TestAnyFilter.create_email(
            peer=('51.4.72.10', 1025),
            mail_from="from@uvigo.gal",
            rcpt_tos=["to1@mail.com", "to2@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient1", "to1@mail.com"), ("Recipient2", "to2@mail.com")],
            email_subject="Valid",
            email_contents="This is a valid mail for testing purposes"
        )
        self.tested_filter.set_initial_data({})
        is_spam = self.tested_filter.filter(envelope)
        self.assertFalse(is_spam, "SPFFilter detected ham as spam")

    def test_valid_2(self):
        envelope = TestAnyFilter.create_email(
            peer=('72.14.192.15', 1025),
            mail_from="from@gmail.com",
            rcpt_tos=["to1@mail.com", "to2@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient1", "to1@mail.com"), ("Recipient2", "to2@mail.com")],
            email_subject="Valid",
            email_contents="This is a valid mail for testing purposes"
        )
        self.tested_filter.set_initial_data(
            {
                'gmail.com': EmailEnvelope.get_all_domain_ip_ranges('gmail.com')
            }
        )
        is_spam = self.tested_filter.filter(envelope)
        self.assertFalse(is_spam, "SPFFilter detected ham as spam")

    def test_spam_1(self):
        envelope = TestAnyFilter.create_email(
            peer=('197.18.20.16', 1025),
            mail_from="from@gmail.com",
            rcpt_tos=["to1@mail.com", "to2@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient1", "to1@mail.com"), ("Recipient2", "to2@mail.com")],
            email_subject="Valid",
            email_contents="This is a valid mail for testing purposes"
        )
        self.tested_filter.set_initial_data(
            {
                'gmail.com': EmailEnvelope.get_all_domain_ip_ranges('gmail.com')
            }
        )
        is_spam = self.tested_filter.filter(envelope)
        self.assertTrue(is_spam, "SPFFilter detected ham as spam")
