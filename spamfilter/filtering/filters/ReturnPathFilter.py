from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.Filter import Filter


class ReturnPathFilter(Filter):
    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This filter determines that an email is spam when the Return-Path header \
        (if any) is different from the sender and the recipients.

        :param envelope: the email to be filtered
        :return: False if the email is not spam, True if it is
        """
        return_path = envelope.email_msg.get("Return-Path")
        if return_path is not None:
            parsed_return_path = self.parse_from_and_to(return_path)
            is_spam = parsed_return_path != envelope.mail_from and parsed_return_path not in envelope.rcpt_tos
            if is_spam:
                print(f"[ ReturnPathFilter ] Return-Path '{parsed_return_path}' is not sender '{envelope.mail_from}' "
                      f"nor a recipient '{envelope.rcpt_tos}'")
                return True
        return False
