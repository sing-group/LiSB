from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class HeloFilter(DBFilter):

    def __init__(self):
        self.table_scheme = {
            'table_name': 'HeloFilter',
            'primary_key': {'name': 'email_addr', 'type': 'text'},
            'attribute_info': [
                {'name': 'helo', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''}
            ]
        }

    def filter(self, envelope: EmailEnvelope) -> bool:
        return False
