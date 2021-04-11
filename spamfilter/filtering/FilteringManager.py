import importlib
import pkgutil
import logging
import threading
import time
from typing import Sequence

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.StorageManager import StorageManager
from spamfilter.filtering.filters.BlackListFilter import BlackListFilter
from spamfilter.filtering.filters.DBFilter import DBFilter
from spamfilter.filtering.filters.Filter import Filter


class FilteringManager:
    filters: Sequence[Filter]
    black_list_filter: BlackListFilter
    enable_threading: int
    storage_mgr: StorageManager

    def __init__(self, enable_threading: int = 1, storing_frequency: int = 300, disabled_filters: list = [],
                 exceptions=None):
        self.enable_threading = enable_threading
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
        filter_classes = {cls.__name__: cls for cls in Filter.__subclasses__() if
                          cls.__name__ not in self.disabled_filters}
        filter_classes.pop('DBFilter')
        filter_classes.update({cls.__name__: cls for cls in DBFilter.__subclasses__() if
                               cls.__name__ not in self.disabled_filters})

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

    def check_if_exception(self, peer_ip, email_address, email_domain):
        return peer_ip in self.exceptions["ip_addresses"] or \
               email_address in self.exceptions["email_addresses"] or \
               email_domain in self.exceptions["email_domains"]

    def apply_filters(self, msg: EmailEnvelope):
        """
        When called, this method applies all filters to the email message. Hence, deciding whether it is spam or not.

        :param msg: The email message to be filtered
        :return: True, if msg is detected as spam; False, if else
        """

        # Check if the peer IP, the email address or the email domain is allowed.
        # If so, let the email pass without filtering
        is_exception = self.check_if_exception(
            peer_ip=msg.peer[0],
            email_address=msg.get_parsed_from(),
            email_domain=msg.get_sender_domain()
        )
        if is_exception:
            return False

        if self.enable_threading:
            n_filtering_threads = len(self.filters)
            all_checks = [0] * n_filtering_threads
            for filter_index in range(n_filtering_threads):
                worker = threading.Thread(
                    target=self.check_if_spam,
                    name=f"FilterThread-{self.filters[filter_index].__class__.__name__}",
                    args=(msg, filter_index, all_checks)
                )
                worker.start()

            n_finished = 0
            while n_finished < n_filtering_threads:
                n_finished = 0
                for check in all_checks:
                    if check == -1:
                        logging.debug(f"Found positive answer! {all_checks}")
                        self.black_list_filter.update_black_list(msg.peer[0])
                        return True
                    elif check == 1:
                        n_finished += 1
        else:
            for flt in self.filters:
                is_spam = flt.filter(msg)
                if is_spam:
                    self.black_list_filter.update_black_list(msg.peer[0])
                    return True

        return False

    def check_if_spam(self, msg, filter_index, all_checks):
        start_time = time.time()
        is_spam = self.filters[filter_index].filter(msg)
        all_checks[filter_index] = -1 if is_spam else 1
        if is_spam:
            logging.debug(f"Finished applying filter after {time.time() - start_time}s")
