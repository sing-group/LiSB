import logging

from core.EmailEnvelope import EmailEnvelope
from core.filtering.filters.Filter import Filter


class ReturnPathFilter(Filter):

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This filter determines that an email is spam when the Return-Path header \
        (if any) is different from the sender and the recipients.

        :param envelope: the email to be filtered
        :return: False if the email is not spam, True if it is
        """

        # Get Return-Path from email. If not None, analyze it
        parsed_return_path = envelope.get_parsed_return_path()
        if parsed_return_path is not None:
            # Check whether it is the sender or one of the recipients. If not, then it is spam
            is_spam = parsed_return_path != envelope.mail_from and parsed_return_path not in envelope.rcpt_tos
            if is_spam:
                logging.info(f"Return-Path '{parsed_return_path}' is not sender '{envelope.mail_from}' "
                             f"nor a recipient '{envelope.rcpt_tos}'")
                return True
        return False
