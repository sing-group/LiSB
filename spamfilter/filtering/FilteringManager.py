import importlib
import pkgutil
from typing import Sequence
from email.message import EmailMessage
from spamfilter.filtering.Filter import Filter


class FilteringManager:
    filters: Sequence[Filter]

    def __init__(self, n_threads: int = 1):
        self.n_threads = n_threads
        self.filters = self.set_up_filters()

    @staticmethod
    def set_up_filters():
        print("[ FilteringManager ] Setting up filters")
        # Get all Filter classes
        filter_classes = {cls.__name__: cls for cls in Filter.__subclasses__()}
        # Import all Filter classes
        for (module_loader, name, ispkg) in pkgutil.iter_modules(["spamfilter.filtering.filters"]):
            importlib.import_module('.' + name, __package__)
        # Instantiate all Filters from filter class names and append to filters list
        filters = list()
        for filter_class in filter_classes:
            print(f"[ FilteringManager ] {filter_class} has been set up")
            filter_object = filter_classes[filter_class]()
            filters.append(filter_object)
        return filters

    def apply_filters(self, msg: EmailMessage):
        is_spam = False
        current_filter = 0
        n_filters = len(self.filters)
        while (current_filter < n_filters) and (not is_spam):
            is_spam = is_spam or self.filters[current_filter].filter(msg)
            current_filter += 1
        return is_spam
