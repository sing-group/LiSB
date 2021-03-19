import ipaddress

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class SPFFilter(DBFilter):
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
        This filter detected whether the senders IP really belongs to its domain by using the Sender Policy Framework (SPF)

        :param envelope: the email to be filtered
        :return: True, if the sender's IP does not belong to the sender's domain (detected as spam). False, if it does.
        """

        # Get sender domain and check if we have data for it. If we don't then look up the IP ranges and return False.
        # If we do then check the IP.
        domain = envelope.get_sender_domain()
        if domain not in self.data:
            self.data[domain] = envelope.get_all_sender_ip_ranges()
            return False
        else:
            sender_ip = envelope.peer[0]
            for ip_range in self.data[domain]:
                if ipaddress.ip_address(sender_ip) in ipaddress.ip_network(ip_range):
                    return False
            print(f"[ SPFFilter ] Sender IP '{sender_ip}' does not belong to the sender domain '{domain}'")
            return True

