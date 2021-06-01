from core.filtering.tests.test_AnyFilter import TestAnyFilter


class TestToFilter(TestAnyFilter):

    def test_spam_1(self):
        invalid = self.create_email(
            peer=self.peer,
            mail_from="from@mail.com",
            rcpt_tos=["to@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Other", "other@mail.com")],
            email_subject="Spam",
            email_contents="This is a spam mail for testing purposes"
        )
        print("TESTING SPAM 1:\n", invalid)
        is_spam = self.tested_filter.filter(invalid)
        self.assertTrue(is_spam, "ToFilter didn't detect spam")

    def test_spam_2(self):
        invalid = self.create_email(
            peer=self.peer,
            mail_from="from@mail.com",
            rcpt_tos=["to1@mail.com", "to2@mail.com"],
            email_from=("Author", "from@mail.com"),
            email_tos=[("Recipient1", "other1@mail.com"), ("Recipient2", "other2@mail.com")],
            email_subject="Spam",
            email_contents="This is a spam mail for testing purposes"
        )
        print("TESTING SPAM 2:\n", invalid)
        is_spam = self.tested_filter.filter(invalid)
        self.assertTrue(is_spam, "ToFilter didn't detect spam")
