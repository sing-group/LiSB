import logging

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.PastFilter import PastFilter


class XFilter(PastFilter):

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This filter detected whether the email's X-Headers (if any) \
        have changed from previous emails from the same domain

        :param envelope: the email to be filtered
        :return: True, if the X-Headers have changed (detected as spam). False, if they haven't.
        """

        # Get X-Headers and analyze them if there are any
        x_headers = envelope.get_x_headers()
        if x_headers:

            # Get sender domain
            domain = envelope.get_sender_domain()

            # If we haven't any previous data from that domain, then store it for next time and return False
            if domain not in self.data:
                self.data[domain] = x_headers

            # If the x-headers are different from the previous data, then return True
            elif set(x_headers) != set(self.data[domain]):
                logging.info(f"The email X-Headers {x_headers} have varied from {domain}'s "
                             f"previous data {self.data[domain]}")
                return True

        return False
