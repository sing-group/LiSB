import ipaddress

import logging
import datetime

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class BlackListFilter(DBFilter):
    black_listed_days: int
    black_listing_threshold: int

    def __init__(self, black_listing_threshold: int, black_listed_days: int):
        """
        This method creates a filter which uses a BlackList based on SpamHaus DROP list
        :param black_listing_threshold: The number of times that a sender can be detected as spam before being always treated as spam
        """
        self.black_listed_days = black_listed_days
        self.black_listing_threshold = black_listing_threshold

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This filter checks whether the envelope peer is black-listed. In that case it detects the email as spam.
        :param envelope: the email to be filtered
        :return: True, if the peer is black-listed. False, if it is not.
        """

        # Get peer ip and check if it is blacklisted or if belongs to a black-listed ip range
        peer_ip: ipaddress.IPv4Address = ipaddress.ip_address(envelope.peer[0])
        if peer_ip.compressed in self.data["ip_addresses"]:
            n_times_detected_as_spam = self.data["ip_addresses"][peer_ip.compressed]["n_times_detected_as_spam"]
            if n_times_detected_as_spam > self.black_listing_threshold:
                logging.info(f"Sender IP {peer_ip} has been previously black-listed")
                return True
        else:
            for ip_range in self.data["ip_ranges"]:
                if peer_ip in ipaddress.ip_network(ip_range):
                    logging.info(f"Sender IP {peer_ip} belongs to a black-listed IP network {ip_range}")
                    return True

        return False

    def set_initial_data(self, data):
        """
        This method overwrites the default set_initial_data method by loading in the initial filter data only the info whose info is not expired
        :param data: the data to be filtered by expiry date and then loaded
        """
        filtered_data = {}
        current_date = datetime.datetime.now()
        for peer in data["ip_addresses"]:
            peer_expiry_date = datetime.datetime.fromisoformat(data["ip_addresses"][peer]["expiry_date"])
            if peer_expiry_date > current_date:
                filtered_data[peer] = data["ip_addresses"][peer]
        self.data["ip_addresses"] = filtered_data
        self.data["ip_ranges"] = data["ip_ranges"]

    def update_black_list(self, peer_ip):
        """
        This method updates the black list by including the peer_ip in it or by incrementing the number of times that it has been detected as spam
        :param peer_ip: the peer IP to be updated in the black list
        """
        if self.data["ip_addresses"].get(peer_ip) is None:
            self.data["ip_addresses"][peer_ip] = {}
            self.data["ip_addresses"][peer_ip]["expiry_date"] = (datetime.datetime.now() + \
                                                                 datetime.timedelta(
                                                                     days=self.black_listed_days
                                                                 )).isoformat()
            n_times_detected_as_spam = 1
        else:
            n_times_detected_as_spam = 1 + self.data["ip_addresses"][peer_ip]["n_times_detected_as_spam"]
        self.data["ip_addresses"][peer_ip]["n_times_detected_as_spam"] = n_times_detected_as_spam
