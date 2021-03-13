from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter


class XFilter(Filter):
    def filter(self, msg: EmailEnvelope) -> bool:
        return False
