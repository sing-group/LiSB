import importlib
import pkgutil
from typing import Sequence

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter
from spamfilter.filtering.filters.Filter import Filter
from spamfilter.filtering.SQLManager import SQLManager


class FilteringManager:
    filters: Sequence[Filter]
    n_threads: int
    sql_mgr: SQLManager

    def __init__(self, n_threads: int = 1):
        self.n_threads = n_threads
        self.sql_mgr = SQLManager("SpamFilter.db")
        self.filters = self.set_up_filters()

    def set_up_filters(self):
        """
        This method sets up all the configured filters

        :return: A list of all the filter objects
        """
        print("[ FilteringManager ] Setting up filters")

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
            print(f"[ FilteringManager ] {filter_class} has been set up")
            filter_object = filter_classes[filter_class]()
            filters.append(filter_object)
            if issubclass(filter_classes[filter_class], DBFilter):
                data = self.sql_mgr.get_info_from_db(filter_object.table_scheme)
                filter_object.set_initial_data(data)
                print(f"[ FilteringManager ] Initial data retrieved for {filter_class}")

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
