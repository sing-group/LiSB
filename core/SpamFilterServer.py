import asyncio
import email
import logging
import logging.config
import logging.handlers
import multiprocessing
import time

from aiosmtpd.controller import Controller

from core.GracefulKiller import GracefulKiller
from core.EmailEnvelope import EmailEnvelope
from core.MailForwarder import MailForwarder
from core.filtering.FilteringManager import FilteringManager


class SpamFilterServer(Controller):
    killer: GracefulKiller

    def __init__(self, conf):
        # Create killer
        self.killer = GracefulKiller()
        # Call parent constructor with Handler and pass killer
        super().__init__(
            handler=SpamFilterHandler(conf, self.killer),
            hostname=conf["server_params"]["local_ip"],
            port=conf["server_params"]["local_port"],
            server_kwargs=conf["server_params"]["SMTP_parameters"]
        )

    def launch_server(self):
        # Star server
        self.start()
        # Wait until the process is killed
        while not self.killer.kill_now:
            pass
        # Shut down gracefully
        self.stop()
        logging.info("Shutting down server...")


class SpamFilterHandler:
    conf: dict
    filtering_mgr: FilteringManager
    forwarder: MailForwarder
    _REJECTION_MSG_RFC_5321 = "450 Requested mail action not taken: mailbox unavailable (e.g., mailbox busy or " \
                              "temporarily blocked for policy reasons)"
    _OK_MSG_RFC_5321 = "250 OK"

    def __init__(self, conf: dict, killer: GracefulKiller):
        logging.info("Setting up SpamFilterServer server")
        self.conf = conf

        # Create mail forwarder, which will forward valid emails
        n_forwarder_threads = conf["forwarding"]["n_forwarder_threads"]
        if n_forwarder_threads == 0:
            n_forwarder_threads = multiprocessing.cpu_count()
        self.forwarder = MailForwarder(
            ip=self.conf["forwarding"]["remote_ip"],
            port=conf["forwarding"]["remote_port"],
            n_forwarder_threads=n_forwarder_threads,
            killer=killer
        )

        # Create filtering manager, which will filter all incoming messages
        self.filtering_mgr = FilteringManager(
            enable_threading=conf["filtering"]["enable_threading"],
            storing_frequency=conf["filtering"]["storing_frequency"],
            black_listing_threshold=conf["filtering"]["black_listing_threshold"],
            black_listed_days=conf["filtering"]["black_listed_days"],
            time_limit=conf["filtering"]["time_limit"],
            disabled_filters=conf["filtering"]["disabled_filters"],
            exceptions=conf["filtering"]["exceptions"],
            killer=killer
        )
        logging.info(
            f"Running SpamFilterServer server on "
            f"{(conf['server_params']['local_ip'], conf['server_params']['local_port'])}"
        )
        logging.info("Waiting for mails to filter...")

    async def handle_DATA(self, server, session, envelope):
        logging.info("A new message has been received")

        # Parse message to EmailEnvelope
        msg_data = email.message_from_bytes(envelope.content)
        parsed_envelope = EmailEnvelope(session.peer, envelope.mail_from, envelope.rcpt_tos, msg_data)

        # Check if parsed message is spam: reject it if it is (code 450), forward it if it isn't
        start_time = time.time()
        is_spam = self.filtering_mgr.apply_filters(parsed_envelope)
        filtering_time = time.time() - start_time
        logging.debug(f"Filtering process lasted for {filtering_time} s")
        if is_spam:
            logging.warning(f"Email from '{envelope.mail_from}' sent from peer {session.peer} was detected as spam. "
                            f"Rejecting message with RFC 5321 code 450...")
            return self._REJECTION_MSG_RFC_5321
        else:
            self.forwarder.forward(parsed_envelope)
            return self._OK_MSG_RFC_5321
