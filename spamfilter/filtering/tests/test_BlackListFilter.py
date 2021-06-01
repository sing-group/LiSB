import datetime
import json
from unittest import TestCase

from spamfilter.filtering.filters.BlackListFilter import BlackListFilter
from spamfilter.filtering.tests.test_AnyFilter import TestAnyFilter


class TestBlackListFilter(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestBlackListFilter, self).__init__(*args, **kwargs)
        self.tested_filter = BlackListFilter(black_listing_threshold=10, black_listed_days=100)
        with open("../../../data/BlackListFilter.json") as file:
            data = json.load(file)
        self.bad_ip = '175.201.54.89'
        self.ip_in_bl_range = '1.19.1.25'
        data["ip_addresses"] = {
            self.bad_ip: {
                "expiry_date": (datetime.datetime.now() + \
                                datetime.timedelta(
                                    days=10
                                )).isoformat(),
                "n_times_detected_as_spam" : 15
            }
        }
        self.tested_filter.set_initial_data(data)

    def test_valid(self):
        envelope = TestAnyFilter.read_test_msg('145.63.42.59')
        is_spam = self.tested_filter.filter(envelope)
        self.assertFalse(is_spam, "BlackListFilter detected ham as spam")

    def test_spam_1(self):
        envelope = TestAnyFilter.read_test_msg(self.bad_ip)
        is_spam = self.tested_filter.filter(envelope)
        self.assertTrue(is_spam, "BlackListFilter detected spam as ham")

    def test_spam_2(self):
        envelope = TestAnyFilter.read_test_msg(self.ip_in_bl_range)
        is_spam = self.tested_filter.filter(envelope)
        self.assertTrue(is_spam, "BlackListFilter detected spam as ham")
