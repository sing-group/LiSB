from email.message import EmailMessage

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class XFilter(DBFilter):

    def __init__(self):
        self.table_scheme = {
            'table_name': 'XFilter',
            'primary_key': {'name': 'id', 'type': 'integer autoincrement'},
            'attribute_info': [
                {'name': 'email_domain', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''},
                {'name': 'x_header', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''}
            ]
        }

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This filter detected whether the email's X-Headers (if any) \
        have changed from previous emails from the same domain

        :param envelope: the email to be filtered
        :return: True, if the X-Headers have changed (detected as spam). False, if they haven't.
        """

        # Get X-Headers and analyze them if there are any
        x_headers = self.get_x_headers(envelope.email_msg)
        if x_headers:

            # Get sender domain
            domain = self.get_domain(envelope.mail_from)

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

    @staticmethod
    def get_x_headers(msg: EmailMessage):
        """
        This utility method gets all x-headers from the passed email message
        :param msg: the email message to extract the x-headers from
        :return: the x-headers in dictionary format
        """
        x_headers = {}
        for (header, value) in msg.items():
            if "X-" in header:
                x_headers[header] = value
        return x_headers
