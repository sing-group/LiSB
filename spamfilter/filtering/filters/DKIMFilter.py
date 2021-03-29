import logging

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.filtering.filters.DBFilter import DBFilter


class DKIMFilter(DBFilter):

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This method determines whether email domain's DKIM parameters have changed from previous times
        :param envelope: the email to be filtered
        :return: True, if the DKIM parameters have varied; False if they haven't or if it is the \
        first time that DKIM is analyzed for that domain
        """
        dkim_params = envelope.get_dkim_params()
        if dkim_params:
            domain = envelope.get_sender_domain()
            if domain not in self.data:
                self.data[domain] = {
                    's': dkim_params['s'],
                    'd': dkim_params['d']
                }
            else:
                if dkim_params['s'] != self.data[domain]['s'] or dkim_params['d'] != self.data[domain]['d']:
                    logging.warning(f"[ DKIMFilter ] Received DKIM params (s:{dkim_params['s']}; d:{dkim_params['d']}) "
                                 f"changed from previous data (s:{self.data[domain]['s']}; d:{self.data[domain]['d']})")
                    return True
        return False
