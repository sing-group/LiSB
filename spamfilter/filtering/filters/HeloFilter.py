from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter


class HeloFilter(Filter):
    def filter(self, msg: EmailEnvelope) -> bool:
        return False
