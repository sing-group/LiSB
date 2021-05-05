from spamfilter.filtering.filters.Filter import Filter


class PastFilter(Filter):
    data: dict = {}

    def set_initial_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

