import smtpd
import email
import email.utils
from email.mime.text import MIMEText
import threading as th
from spamfilter.MailForwarder import MailForwarder


class SpamFilter(smtpd.SMTPServer):

    _REJECTION_MSG_RFC_5321 = "450 Requested mail action not taken: mailbox unavailable (e.g., mailbox busy or " \
                              "temporarily blocked for policy reasons) "

    def __init__(self, localaddr, remoteaddr, data_size_limit=smtpd.DATA_SIZE_DEFAULT,
                 map=None, enable_SMTPUTF8=False, decode_data=False):
        print(f"[ {th.current_thread().name} ] Running SpamFilter on {localaddr}")
        print(f"[ {th.current_thread().name} ] Waiting for mails to filter...")
        super().__init__(localaddr, remoteaddr, data_size_limit, map, enable_SMTPUTF8, decode_data)
        self.forwarder = MailForwarder(self._remoteaddr[0], self._remoteaddr[1], 4)

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print(f"[ {th.current_thread().name} ] A new message has been received")
        msg = email.message_from_bytes(data)
        if self.filter_msg(msg):
            print(f"[ {th.current_thread().name} ] Spam detected: rejecting message (450)...")
            return self._REJECTION_MSG_RFC_5321
        else:
            self.forwarder.forward(msg)
            return None

    @staticmethod
    def filter_msg(msg):
        return True

