from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.Filter import Filter


class XFilter(Filter):
    def filter(self, envelope: EmailEnvelope) -> bool:
        return False
