import importlib
import pkgutil
import logging
from typing import Sequence


from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.StorageManager import StorageManager
from spamfilter.filtering.filters.DBFilter import DBFilter
from spamfilter.filtering.filters.Filter import Filter


class FilteringManager:
    filters: Sequence[Filter]
    n_threads: int
    storage_mgr: StorageManager

    def __init__(self, n_threads: int = 1, storing_frequency: int = 300):
        self.n_threads = n_threads
        self.storage_mgr = StorageManager("data/", storing_frequency)
        self.filters = self.set_up_filters()
        self.storage_mgr.launch_storage_daemon(self.filters)

    def set_up_filters(self):
        """
        This method sets up all the configured filters

        :return: A list of all the filter objects
        """
        logging.info("[ FilteringManager ] Setting up filters")

        # Import all Filter classes
        for (module_loader, name, ispkg) in pkgutil.iter_modules(["spamfilter.filtering.filters"]):
            importlib.import_module('.' + name, __package__)

        # Load all Filter classes
        filter_classes = {cls.__name__: cls for cls in Filter.__subclasses__()}
        filter_classes.pop('DBFilter')
        filter_classes.update({cls.__name__: cls for cls in DBFilter.__subclasses__()})

        # Instantiate all Filters from filter class names and append to filters list
        # Get past data for filters that need it
        filters = list()
        for filter_class in filter_classes:
            logging.info(f"[ FilteringManager ] {filter_class} has been set up")
            filter_object = filter_classes[filter_class]()
            filters.append(filter_object)
            if issubclass(filter_classes[filter_class], DBFilter):
                data = self.storage_mgr.load_data(filter_class)
                filter_object.set_initial_data(data)
        return filters

    def apply_filters(self, msg: EmailEnvelope):
        """
        When called, this method applies all filters to the email message. Hence, deciding whether it is spam or not.

        :param msg: The email message to be filtered
        :return: True, if msg is detected as spam; False, if else
        """
        is_spam = False
        current_filter = 0
        n_filters = len(self.filters)
        while (current_filter < n_filters) and (not is_spam):
            is_spam = is_spam or self.filters[current_filter].filter(msg)
            current_filter += 1
        return is_spam
