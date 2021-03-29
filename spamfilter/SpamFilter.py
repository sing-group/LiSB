import json
import logging
import logging.config
import logging.handlers
import os
import smtpd
import email
import email.utils

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.MailForwarder import MailForwarder
from spamfilter.filtering.FilteringManager import FilteringManager


class SpamFilter(smtpd.SMTPServer):
    filtering_mgr: FilteringManager
    forwarder: MailForwarder
    _REJECTION_MSG_RFC_5321 = "450 Requested mail action not taken: mailbox unavailable (e.g., mailbox busy or " \
                              "temporarily blocked for policy reasons)"

    def __init__(self, localaddr, remoteaddr, data_size_limit=smtpd.DATA_SIZE_DEFAULT,
                 map=None, enable_SMTPUTF8=False, decode_data=False):

        # Config logging
        SpamFilter.config_logging()

        logging.info("[ SpamFilter ] Setting up SpamFilter server")

        # Call parent constructor
        super().__init__(localaddr, remoteaddr, data_size_limit, map, enable_SMTPUTF8, decode_data)

        # Create mail forwarder, which will forward valid emails
        self.forwarder = MailForwarder(self._remoteaddr[0], self._remoteaddr[1], 1)

        # Create filtering manager, which will filter all incoming messages
        self.filtering_mgr = FilteringManager(storing_frequency=600)
        logging.info(f"[ SpamFilter ] Running SpamFilter server on {localaddr}")
        logging.info("[ SpamFilter ] Waiting for mails to filter...")

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """
        This method processes incoming email. It determines wether it is spam or not.

        :param peer: The remote host’s address
        :param mailfrom: The SMTP envelope originator
        :param rcpttos: The SMTP envelope recipients
        :param data: The contents of the email in RFC 5321 format
        :param kwargs: Arbitrary keyword arguments
        :return: None to request a normal 250 Ok response, RFC 53214-compliant 450 code when spam is detected
        """

        logging.info("[ SpamFilter ] A new message has been received")

        # Parse message to EmailEnvelope
        msg_data = email.message_from_bytes(data)
        msg = EmailEnvelope(peer, mailfrom, rcpttos, msg_data, **kwargs)

        # Check if parsed message is spam: reject it if it is (code 450), forward it if it isn't
        is_spam = self.filtering_mgr.apply_filters(msg)
        if is_spam:
            logging.warning("[ SpamFilter ] Spam detected: rejecting message (450)...")
            return self._REJECTION_MSG_RFC_5321
        else:
            self.forwarder.forward(msg)
            return None

    @staticmethod
    def config_logging():

        # Create logs directory if it doesn't exist
        path = 'logs/'
        if not os.path.exists(path):
            os.makedirs(path)

        with open('conf/logging.json', 'r') as file:
            config = json.load(file)

        logging.config.dictConfig(config)
