from spamfilter.filtering.filters.Filter import Filter


class DBFilter(Filter):
    table_scheme: dict
    data: dict

    def set_initial_data(self, data):
        self.data = data

    def get_data(self):
        return self.data