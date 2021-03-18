from email.message import EmailMessage

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering import DBFilter


class XFilter(DBFilter):

    def __init__(self):
        self.table_scheme = {
            'table_name': 'XFilter',
            'primary_key': {'name': 'id', 'type': 'integer autoincrement'},
            'attribute_info': [
                {'name': 'email_domain', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''},
                {'name': 'x_header', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''},
                {'name': 'x_value', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''}
            ]
        }

    def filter(self, envelope: EmailEnvelope) -> bool:
        x_headers = self.get_x_headers(envelope.email_msg)

        if x_headers:
            domain = self.get_domain(envelope.mail_from)

            if domain not in self.data:
                self.data[domain] = x_headers
            else:

                for x_header in x_headers:
                    if self.data[domain]['']:
                        pass

        return False

    @staticmethod
    def get_x_headers(msg: EmailMessage):
        x_headers = {}
        for (header, value) in msg.items():
            if "X-" in header:
                x_headers[header] = value
        return x_headers
