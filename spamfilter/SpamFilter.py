import logging
import logging.config
import logging.handlers
import multiprocessing
import os
import smtpd
import email
import email.utils

from spamfilter.EmailEnvelope import EmailEnvelope
from spamfilter.MailForwarder import MailForwarder

from spamfilter.filtering.FilteringManager import FilteringManager


class SpamFilter(smtpd.SMTPServer):
    conf: dict
    filtering_mgr: FilteringManager
    forwarder: MailForwarder
    _REJECTION_MSG_RFC_5321 = "450 Requested mail action not taken: mailbox unavailable (e.g., mailbox busy or " \
                              "temporarily blocked for policy reasons)"

    def __init__(self, conf: dict):

        logging.info("Setting up SpamFilter server")
        self.conf = conf

        # Call parent constructor
        super().__init__(
            localaddr=(conf["server_params"]["local_ip"], conf["server_params"]["local_port"]),
            remoteaddr=(conf["forwarding"]["remote_ip"], conf["forwarding"]["remote_port"]),
            data_size_limit=conf["server_params"]["data_size_limit"],
            map=conf["server_params"]["map"],
            enable_SMTPUTF8=conf["server_params"]["enable_SMTPUTF8"],
            decode_data=conf["server_params"]["decode_data"]
        )

        # Create mail forwarder, which will forward valid emails
        n_forwarder_threads = conf["forwarding"]["n_forwarder_threads"]
        if n_forwarder_threads == 0:
            n_forwarder_threads = multiprocessing.cpu_count()
        self.forwarder = MailForwarder(
            ip=self._remoteaddr[0],
            port=self._remoteaddr[1],
            n_forwarder_threads=n_forwarder_threads
        )

        # Create filtering manager, which will filter all incoming messages
        n_filtering_threads = conf["filtering"]["n_filtering_threads"]
        if n_filtering_threads == 0:
            n_filtering_threads = multiprocessing.cpu_count()
        self.filtering_mgr = FilteringManager(
            n_filtering_threads=n_filtering_threads,
            storing_frequency=conf["filtering"]["storing_frequency"],
            disabled_filters=conf["filtering"]["disabled_filters"],
            exceptions=conf["filtering"]["exceptions"]
        )
        logging.info(f"Running SpamFilter server on {self._localaddr}")
        logging.info("Waiting for mails to filter...")

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

        logging.info("A new message has been received")

        # Parse message to EmailEnvelope
        msg_data = email.message_from_bytes(data)
        msg = EmailEnvelope(peer, mailfrom, rcpttos, msg_data, **kwargs)

        # Check if parsed message is spam: reject it if it is (code 450), forward it if it isn't
        is_spam = self.filtering_mgr.apply_filters(msg)
        if is_spam:
            logging.warning("Spam detected: rejecting message (450)...")
            return self._REJECTION_MSG_RFC_5321
        else:
            self.forwarder.forward(msg)
            return None
