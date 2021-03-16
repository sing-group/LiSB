import collections

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter


class ToFilter(Filter):

    def filter(self, msg: EmailEnvelope) -> bool:
        """
        This filter checks whether the envelope recipients are the same as the email message recipients.
        If not, this indicates that the email may be spam.

        :param msg: The message to be filtered
        :return: False if the recipients are the same, True if else (Spam)
        """

        msg_tos = [self.parse_from_and_to(to_parse) for to_parse in msg.email_msg.get("To").split(",")]

        if set(msg.rcpt_tos) != set(msg_tos):
            print(f"[ ToFilter ] Recipients differ: {msg.rcpt_tos} in envelope VS. {msg_tos} in message")
            return True

        return False
