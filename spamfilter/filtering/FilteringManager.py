import importlib
import pkgutil
import logging
from typing import Sequence

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.StorageManager import StorageManager
from spamfilter.filtering.filters.BlackListFilter import BlackListFilter
from spamfilter.filtering.filters.DBFilter import DBFilter
from spamfilter.filtering.filters.Filter import Filter


class FilteringManager:
    filters: Sequence[Filter]
    black_list_filter: BlackListFilter
    n_filtering_threads: int
    storage_mgr: StorageManager

    def __init__(self, n_filtering_threads: int = 1, storing_frequency: int = 300, disabled_filters: list = [],
                 exceptions=None):
        self.n_filtering_threads = n_filtering_threads
        self.disabled_filters = disabled_filters
        self.exceptions = exceptions
        self.storage_mgr = StorageManager("data/", storing_frequency)
        self.set_up_filters()
        self.storage_mgr.launch_storage_daemon(self.filters)

    def set_up_filters(self):
        """
        This method sets up all the configured filters

        :return: A list of all the filter objects
        """
        logging.info("Setting up filters")

        # Import all Filter classes
        for (module_loader, name, ispkg) in pkgutil.iter_modules(["spamfilter.filtering.filters"]):
            importlib.import_module('.' + name, __package__)

        # Load all Filter classes
        filter_classes = {cls.__name__: cls for cls in Filter.__subclasses__()}
        filter_classes.pop('DBFilter')
        filter_classes.update({cls.__name__: cls for cls in DBFilter.__subclasses__()})

        # Instantiate all Filters from filter class names and append to filters list
        # Get past data for filters that need it
        self.filters = list()
        for filter_class in filter_classes:
            logging.info(f"{filter_class} has been set up")

            # Store BlackListFilter independently
            if filter_classes[filter_class] is BlackListFilter:
                self.black_list_filter = filter_object = filter_classes[filter_class](limit=0)
            else:
                filter_object = filter_classes[filter_class]()
            self.filters.append(filter_object)

            if issubclass(filter_classes[filter_class], DBFilter):
                data = self.storage_mgr.load_data(filter_class)
                filter_object.set_initial_data(data)

    def apply_filters(self, msg: EmailEnvelope):
        """
        When called, this method applies all filters to the email message. Hence, deciding whether it is spam or not.

        :param msg: The email message to be filtered
        :return: True, if msg is detected as spam; False, if else
        """

        # Check if the peer IP, the email address or the email domain is allowed.
        # If so, let the email pass without filtering
        is_exception = self.check_if_is_exception(
            peer_ip=msg.peer[0],
            email_address=msg.get_parsed_from(),
            email_domain=msg.get_sender_domain()
        )
        if is_exception:
            return False

        is_spam = False
        current_filter = 0
        n_filters = len(self.filters)
        while (current_filter < n_filters) and (not is_spam):
            is_spam = is_spam or self.filters[current_filter].filter(msg)
            current_filter += 1
        if is_spam:
            self.black_list_filter.update_black_list(msg.peer[0])
        return is_spam

    def check_if_is_exception(self, peer_ip, email_address, email_domain):
        return peer_ip in self.exceptions["ip_addresses"] or \
               email_address in self.exceptions["email_addresses"] or \
               email_domain in self.exceptions["email_domains"]
