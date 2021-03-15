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
        envelope_tos = self.parse_from_and_to(msg.rcpt_tos)
        msg_tos = self.parse_from_and_to(msg.email_msg.get("To"))

        if envelope_tos != msg_tos:
            print(f"[ FromFilter ] Recipients differ: '{envelope_tos}' in envelope VS. '{msg_tos}' in message")
            return True

        return False
