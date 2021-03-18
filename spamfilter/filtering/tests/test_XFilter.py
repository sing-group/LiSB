from spamfilter.filtering.filters.XFilter import XFilter
from spamfilter.filtering.tests.test_AnyFilter import TestAnyFilter


class TestXFilter(TestAnyFilter):

    def test_valid_1(self):
        valid = self.create_email(
            peer=self.this_ip,
            mail_from="from@mail.com",
            rcpt_tos=["to@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient", "to@mail.com")],
            email_subject="Spam",
            email_contents="This is a valid mail for testing purposes",
            other_headers={
                'X-Header1': 'value1',
                'X-Header2': 'value2',
                'X-Header3': 'value3'
            }
        )
        x_filter: XFilter = self.tested_filter
        x_filter.set_initial_data(
            {
                "mail.com": {'X-Header1': 'value1', 'X-Header2': 'value2', 'X-Header3': 'value3'}
            }
        )
        x_filter.filter(valid)
        is_spam = self.tested_filter.filter(valid)
        self.assertFalse(is_spam, "XFilter failed when checking ham")

    def test_valid_2(self):
        valid = self.create_email(
            peer=self.this_ip,
            mail_from="from@mail.com",
            rcpt_tos=["to@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient", "to@mail.com")],
            email_subject="Spam",
            email_contents="This is a valid mail for testing purposes",
            other_headers={}
        )
        x_filter: XFilter = self.tested_filter
        x_filter.set_initial_data(
            {
                "mail.com": {'X-Header1': 'value1', 'X-Header2': 'value2', 'X-Header3': 'value3'}
            }
        )
        x_filter.filter(valid)
        is_spam = self.tested_filter.filter(valid)
        self.assertFalse(is_spam, "XFilter failed when checking ham")

    def test_spam_1(self):
        invalid = self.create_email(
            peer=self.this_ip,
            mail_from="from@mail.com",
            rcpt_tos=["to@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient", "to@mail.com")],
            email_subject="Spam",
            email_contents="This is a spam mail for testing purposes",
            other_headers={
                'X-Header1': 'value1',
                'X-Header2': 'value2',
                'X-Header3': 'value3'
            }
        )
        x_filter: XFilter = self.tested_filter
        x_filter.set_initial_data(
            {
                "mail.com": {'X-Header1': 'value1', 'X-Header2': 'value2'}
            }
        )
        x_filter.filter(invalid)
        is_spam = self.tested_filter.filter(invalid)
        self.assertTrue(is_spam, "XFilter failed when checking spam")

    def test_spam_2(self):
        invalid = self.create_email(
            peer=self.this_ip,
            mail_from="from@mail.com",
            rcpt_tos=["to@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient", "to@mail.com")],
            email_subject="Spam",
            email_contents="This is a spam mail for testing purposes",
            other_headers={
                'X-SomeOtherHeader': 'value1',
                'X-Header2': 'value2',
                'X-Header3': 'value3'
            }
        )
        x_filter: XFilter = self.tested_filter
        x_filter.set_initial_data(
            {
                "mail.com": {'X-Header1': 'value1', 'X-Header2': 'value2', 'X-Header3': 'value3'}
            }
        )
        x_filter.filter(invalid)
        is_spam = self.tested_filter.filter(invalid)
        self.assertTrue(is_spam, "XFilter failed when checking spam")
