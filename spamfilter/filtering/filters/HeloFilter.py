from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class HeloFilter(DBFilter):

    def filter(self, envelope: EmailEnvelope) -> bool:
        return False
