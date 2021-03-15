from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import Filter


class FromFilter(Filter):

    def filter(self, msg: EmailEnvelope) -> bool:
        """
        This filter checks whether the envelope originator is the same as the email message originator.
        If not, this indicates that the email may be spam.

        :param msg: The message to be filtered
        :return: False if the originators are the same, True if else (Spam)
        """

        parsed_msg_from = self.parse_from_and_to(msg.email_msg.get("From"))

        if msg.mail_from != parsed_msg_from:
            print(f"[ FromFilter ] Senders differ: '{msg.mail_from}' in envelope VS. '{parsed_msg_from}' in message")
            return True

        return False
