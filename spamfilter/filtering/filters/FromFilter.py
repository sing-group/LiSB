from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter


class FromFilter(Filter):

    def filter(self, msg: EmailEnvelope) -> bool:
        """
        This filter checks whether the envelope originator is the same as the email message originator.
        This indicates that the email may be spam.

        :param msg: The message to be filtered
        :return: False if the originators are the same, True if else (Spam)
        """
        envelope_from = self.parse_from(msg.mail_from)
        msg_from = self.parse_from(msg.email_msg.get("From"))

        if envelope_from != msg_from:
            print(f"[ FromFilter ] Froms differ: '{envelope_from}' in envelope VS. '{msg_from}' in message")
            return True

        return False
