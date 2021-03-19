from spamfilter.filtering.filters.Filter import Filter


class DBFilter(Filter):
    data: dict = {}

    def set_initial_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

    def debug(self):
        print(f"Current contents of dictionary:\n{self.data}\n\n")
