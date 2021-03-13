from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter


class SPFFilter(Filter):
    def filter(self, msg: EmailEnvelope) -> bool:
        return False

