from email.message import EmailMessage

from spamfilter.filtering.Filter import Filter


class PortFilter(Filter):

    def filter(self, msg: EmailMessage) -> bool:
        return False
