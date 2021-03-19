from email.message import EmailMessage

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class XFilter(DBFilter):

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

            # If the number of received x-headers has varied from the past number of x-headers,
            # they must have changed. Therefore return True
            elif len(x_headers) != len(self.data[domain]):
                print(f"[ XFilter ] The number of X-Headers is different")
                return True

            # If the number is the same, then check that the headers are the same
            else:
                for (x_header, value) in x_headers.items():
                    if x_header not in self.data[domain]:
                        print(f"[ XFilter ] '{x_header}' header was not present in past communications")
                        return True
        return False
