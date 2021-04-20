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
    black_list_filter: BlackListFilter = None
    enable_threading: int
    storage_mgr: StorageManager

    def __init__(self, enable_threading: int = 1, black_listing_threshold: int = 10, black_listed_days: int = 10,
                 time_limit: float = 1.5, storing_frequency: int = 300, disabled_filters: list = [], exceptions=None):
        self.enable_threading = enable_threading
        self.black_listing_threshold = black_listing_threshold
        self.black_listed_days = black_listed_days
        self.time_limit = time_limit
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
                self.black_list_filter = filter_object = filter_classes[filter_class](
                    black_listing_threshold=self.black_listing_threshold,
                    black_listed_days=self.black_listed_days
                )
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
        is_exception = self.check_if_exception(
            peer_ip=msg.peer[0],
            email_address=msg.get_parsed_from(),
            email_domain=msg.get_sender_domain()
        )
        if is_exception:
            return False

        # Apply filters to the message.
        # If threading is enabled, launch a thread for each filter.
        # If not, then apply filters sequentially.
        is_spam = False
        if self.enable_threading:

            # Launch a thread for each filter
            n_filtering_threads = len(self.filters)
            all_checks = [0] * n_filtering_threads
            for filter_index in range(n_filtering_threads):
                worker = threading.Thread(
                    target=self.check_if_spam,
                    name=f"FilterThread-{self.filters[filter_index].__class__.__name__}",
                    args=(msg, filter_index, all_checks)
                )
                worker.start()

            # Check the results of each thread while:
            #   - All of them haven't finished
            #   - One detects spam
            #   - The time limit isn't exceeded
            n_finished = 0
            start_time = time.time()
            current_time = 0.0
            while not is_spam and n_finished < n_filtering_threads and current_time < self.time_limit:
                n_finished = 0
                filter_index = 0
                n_filters = len(self.filters)
                while not is_spam and filter_index < n_filters and current_time < self.time_limit:
                    is_spam = all_checks[filter_index] == -1
                    if all_checks[filter_index] == 1:
                        n_finished += 1
                    filter_index += 1
                    current_time = time.time() - start_time
        else:

            # Apply all filters while spam isn't detected and there are filters to apply
            n_filters = len(self.filters)
            current_filter = 0
            start_time = time.time()
            current_time = 0.0
            while not is_spam and current_filter < n_filters and current_time < self.time_limit:
                is_spam = self.filters[current_filter].filter(msg)
                current_time = time.time() - start_time
                current_filter += 1

        # If spam is detected, update the black list (if needed) and return True
        if is_spam:
            if self.black_list_filter:
                self.black_list_filter.update_black_list(msg.peer[0])
            return True

        # If the time limit was exceeded, log debug message
        if current_time >= self.time_limit:
            logging.debug(f"Time limit ({self.time_limit}) exceeded in filtering process ({current_time}). "
                          f"Hence, returning False.")

        return False

    def check_if_exception(self, peer_ip, email_address, email_domain):
        """
        This method checks whether the peer IP, the email address or the email domain from which the email is sent is one of the exceptions described in the 'conf/filterin.json' file.
        :param peer_ip: the peer IP which sent the email
        :param email_address: the email sender's email address
        :param email_domain: the email sender's domain
        :return: True, if it's an exception; False, if it isn't
        """
        return peer_ip in self.exceptions["ip_addresses"] or \
               email_address in self.exceptions["email_addresses"] or \
               email_domain in self.exceptions["email_domains"]

    def check_if_spam(self, msg, filter_index, all_checks):
        """
        This method is executed by the filter threads when 'enable_threading' is set to True for the FilteringManager.
        Each thread applies one of the filters to the email message and determines whether it is spam or not.
        :param msg: the email message to be filtered
        :param filter_index: the index of the specific filter
        :param all_checks: a list of 0s, where the thread will write the result of the filter to the filter_index position. It will write -1 if msg is spam and 1 if it isn't.
        """
        is_spam = self.filters[filter_index].filter(msg)
        all_checks[filter_index] = -1 if is_spam else 1
