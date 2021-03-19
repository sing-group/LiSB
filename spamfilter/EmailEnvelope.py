from email.message import EmailMessage
from typing import Sequence, re

import dns


class EmailEnvelope:
    peer: str = None
    mail_from: str = None
    rcpt_tos: Sequence[str] = None
    email_msg: EmailMessage = None
    kwargs = None
    _sender_domain = None

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
        self._sender_domain = mail_from.split("@")[1]

    def __str__(self):
        msg_verbose = "======================================================\n" \
                      f"Peer: {self.peer}\n" \
                      f"Mail From: {self.mail_from}\n" \
                      f"Recipients: {self.rcpt_tos}\n" \
                      "------------------------------------------------------\n" \
                      f"{self.email_msg}\n\n" \
                      f"-----------------------------------------------------"
        return msg_verbose

    def get_sender_domain(self):
        return self._sender_domain

    def get_parsed_from(self):
        """
        This method returns the parsed 'From' header (just email address)

        :return: The parsed 'From' header
        """
        value = self.email_msg.get('From')
        return EmailEnvelope.get_parsed(value)

    def get_parsed_to_list(self):
        """
        This method returns the parsed 'To' header (just email addresses)

        :return: The list of parsed recipients
        """
        return [EmailEnvelope.get_parsed(to_parse) for to_parse in self.email_msg.get("To").split(",")]

    def get_parsed_return_path(self):
        """
        This method returns the parsed 'Return-Path' to header (just email address), if any

        :return: The parsed 'Return-Path' header. None if the email doesn't have it.
        """
        value = self.email_msg.get('Return-Path')
        return EmailEnvelope.get_parsed(value)

    @staticmethod
    def get_parsed(header_value):
        """
        This utility method parses 'From', 'To' and 'Return-Path' headers to only email format
        :param header: the header to be parsed
        :return: The parsed header
        """
        if header_value is not None:
            aux_list = header_value.split("<")
            list_length = len(aux_list)
            return aux_list[0] if list_length == 1 else aux_list[list_length - 1][:-1]
        return None

    def get_x_headers(self):
        """
        This method gets all X-headers from the email message
        :return: the X-headers in dictionary format
        """
        x_headers = {}
        for (header, value) in self.email_msg.items():
            if "X-" in header:
                x_headers[header] = value
        return x_headers

    def get_dkim_params(self):
        """
        This method gets all DKIM parameters from the email message
        :return: the DKIM parameters in dictionary format
        """
        dkim_params = {}
        for to_parse in self.email_msg.get('DKIM-Signature').split(';'):
            parsed = to_parse.replace("\n", "").strip().split('=')
            dkim_params[parsed[0]] = parsed[1].strip()
        return dkim_params

    def get_all_sender_ip_ranges(self):
        """
        This method gets through DNS queries all of the used ip ranges of the sender domain according to SPF.

        :return: a list of all the sender domain's ip ranges
        """
        return EmailEnvelope.get_all_domain_ip_ranges(self._sender_domain)

    @staticmethod
    def get_all_domain_ip_ranges(domain):
        """
        This utility method gets through DNS queries all of the used ip ranges of a domain according to SPF.

        :param domain: the domain to look the ip ranges for
        :return: a list of all the domain's ip ranges
        """
        dig_data = {}
        for to_parse in dns.resolver.query(domain, 'TXT'):
            parsed = str(to_parse).replace("\"", "").split('=', 1)
            dig_data[parsed[0]] = parsed[1]
        ip_ranges = re.findall("ip[4|6]:([^ ]+)", dig_data['v'])
        includes = re.findall("include:([^ ]+)", dig_data['v'])
        redirect = re.findall("redirect=([^ ]+)", dig_data['v'])
        if redirect:
            ip_ranges.extend(EmailEnvelope.get_all_domain_ip_ranges(redirect[0]))
        if includes:
            for include in includes:
                ip_ranges.extend(EmailEnvelope.get_all_domain_ip_ranges(include))
        return ip_ranges
