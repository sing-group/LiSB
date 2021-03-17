from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.Filter import Filter


class SPFFilter(Filter):
    def filter(self, envelope: EmailEnvelope) -> bool:
        return False

