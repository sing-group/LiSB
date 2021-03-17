import collections

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.Filter import Filter


class ToFilter(Filter):

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This filter checks whether the envelope recipients are the same as the email message recipients.
        If not, this indicates that the email may be spam.

        :param envelope: The message to be filtered
        :return: False if the recipients are the same, True if else (Spam)
        """

        msg_tos = [self.parse_from_and_to(to_parse) for to_parse in envelope.email_msg.get("To").split(",")]

        if set(envelope.rcpt_tos) != set(msg_tos):
            print(f"[ ToFilter ] Recipients differ: {envelope.rcpt_tos} in envelope VS. {msg_tos} in message")
            return True

        return False
