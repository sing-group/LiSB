import ipaddress

import logging

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class BlackListFilter(DBFilter):
    limit: int

    def __init__(self, limit: int):
        """
        This method creates a filter which uses a BlackList based on SpamHaus DROP list
        :param limit: The number of times that a sender can be detected as spam before being always treated as spam
        """
        self.limit = limit

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This filter checks whether the envelope peer is black-listed. In that case it detects the email as spam.
        :param envelope: the email to be filtered
        :return: True, if the peer is black-listed. False, if it is not.
        """

        # Get peer and check if it is blacklisted.
        peer = envelope.peer[0]

        # If it is, increment the number of times that it has been detected as spam and check if it exceeds the limit.
        if peer not in self.data:
            return False
        else:
            n_times_detected_as_spam = self.data[peer] + 1
            self.data[peer] = n_times_detected_as_spam
            if n_times_detected_as_spam > self.limit:
                logging.warning(f"Sender IP has been black-listed'")
                return True

        return False

    def add_to_black_list(self, peer_ip):
        self.data[peer_ip] = 0
