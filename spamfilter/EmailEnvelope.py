from email.message import EmailMessage
from typing import Sequence


class EmailEnvelope:
    peer: str = None
    mail_from: str = None
    rcpt_tos: Sequence[str] = None
    email_msg: EmailMessage = None
    kwargs = None

    def __init__(self, peer, mail_from, rcpt_tos, email_msg, **kwargs):
        """
        This method creates a container for the email and envelope data

        :param peer: the remote host’s address
        :param mail_from: the SMTP envelope originator
        :param rcpt_tos: the SMTP envelope recipients
        :param email_msg: the contents of the email in RFC 5321 format
        :param kwargs: arbitrary keyword arguments
        """
        self.peer = peer
        self.mail_from = mail_from
        self.rcpt_tos = rcpt_tos
        self.email_msg = email_msg
        self.kwargs = kwargs
