from spamfilter.filtering.tests.test_AnyFilter import TestAnyFilter


class TestFromFilter(TestAnyFilter):

    def test_spam_1(self):
        invalid = self.create_email(
            peer=self.this_ip,
            mail_from="from@mail.com",
            rcpt_tos=["to@mail.com"],
            email_from=("Other", "other_from@mail.com"),
            email_tos=[("Recipient", "to@mail.com")],
            email_subject="Spam",
            email_contents="This is a spam mail for testing purposes"
        )
        print("TESTING SPAM 1:\n", invalid)
        is_spam = self.tested_filter.filter(invalid)
        self.assertTrue(is_spam, "FromFilter didn't detect spam")
