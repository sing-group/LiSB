from spamfilter.filtering.filters.FromFilter import FromFilter
from spamfilter.filtering.tests.TestAnyFilter import TestAnyFilter


class TestFromFilter(TestAnyFilter):

    def test_valid_1(self):
        invalid = self.create_email(
            peer=self.this_ip,
            mail_from="from@mail.com",
            rcpt_tos="to@mail.com",
            email_from=("Author", "from@mail.com"),
            email_tos=("Recipient", "to@mail.com"),
            email_subject="Spam",
            email_contents="This is a valid mail for testing purposes"
        )
        not_spam = self.tested_filter.filter(invalid)
        self.assertFalse(not_spam, "FromFilter detected spam incorrectly")

    def test_spam_1(self):
        invalid = self.create_email(
            peer=self.this_ip,
            mail_from="from@mail.com",
            rcpt_tos="to@mail.com",
            email_from=("Other", "other_from@mail.com"),
            email_tos=("Recipient", "to@mail.com"),
            email_subject="Spam",
            email_contents="This is a spam mail for testing purposes"
        )
        is_spam = self.tested_filter.filter(invalid)
        self.assertTrue(is_spam, "FromFilter didn't detect spam")
