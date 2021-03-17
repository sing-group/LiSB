from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.Filter import Filter


class DKIMFilter(Filter):
    def filter(self, envelope: EmailEnvelope) -> bool:
        return False
