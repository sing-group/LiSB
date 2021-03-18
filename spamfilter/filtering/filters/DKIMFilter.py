from email.message import EmailMessage

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class DKIMFilter(DBFilter):

    def __init__(self):
        self.table_scheme = {
            'table_name': 'DKIMFilter',
            'primary_key': {'name': 'email_domain', 'type': 'text'},
            'attribute_info': [
                {'name': 's', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''},
                {'name': 'd', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''}
            ]
        }

    def filter(self, envelope: EmailEnvelope) -> bool:
        dkim_params = DKIMFilter.get_dkim_params(envelope.email_msg)
        if dkim_params:
            domain = DKIMFilter.get_domain(envelope.mail_from)
            if domain not in self.data:
                self.data[domain] = {
                    's': dkim_params['s'],
                    'd': dkim_params['d']
                }
            else:
                if dkim_params['s'] != self.data[domain]['s'] or dkim_params['d'] != self.data[domain]['d']:
                    print(f"[ DKIMFilter ] Received DKIM params (s:{dkim_params['s']}; d:{dkim_params['d']}) "
                          f"changed from previous data (s:{self.data[domain]['s']}; d:{self.data[domain]['d']})")
                    return True
        return False

    @staticmethod
    def get_dkim_params(msg: EmailMessage):
        """
        This utility method gets all DKIM parameters from the passed email message
        :param msg: the email message to extract the DKIM parameters from
        :return: the DKIM parameters in dictionary format
        """
        dkim_params = {}
        for to_parse in msg.get('DKIM-Signature').split(';'):
            parsed = to_parse.replace("\n", "").strip().split('=')
            dkim_params[parsed[0]] = parsed[1].strip()
        return dkim_params
