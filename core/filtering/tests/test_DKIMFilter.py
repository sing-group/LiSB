
from core.filtering.tests.test_AnyFilter import TestAnyFilter


class TestDKIMFilter(TestAnyFilter):

    def test_valid_1(self):
        envelope = TestAnyFilter.read_test_msg()
        self.tested_filter.set_initial_data({})
        is_spam = self.tested_filter.filter(envelope)
        self.assertFalse(is_spam, "DKIMFilter detected ham as spam")

    def test_valid_2(self):
        envelope = TestAnyFilter.read_test_msg()
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
        envelope = TestAnyFilter.read_test_msg()
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