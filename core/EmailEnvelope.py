import re
import sys
import dns.resolver
from typing import Sequence
from email.message import EmailMessage


class EmailEnvelope:
    peer: str = None
    mail_from: str = None
    rcpt_tos: Sequence[str] = None
    email_msg: EmailMessage = None
    kwargs = None
    _sender_domain = None
    all_content_types = [
        "text/html", "text/plain", "multipart/mixed", "application/octet-stream",
        "multipart/alternative", "multipart/related", "image/jpeg", "image/gif", "message/rfc822",
        "text/plain charset=us-ascii", "image/png", "text/x-vcard", "image/bmp",
        "application/x-zip-compressed", "multipart/signed", "application/pgp-signature",
        "text/enriched", "application/ms-tnef", "video/mng", "application/x-pkcs7-signature",
        "multipart/report", "message/delivery-status", "text/rfc822-headers",
        "application/x-java-applet", "application/x-patch"
    ]
    all_extension_types = [
        "txt", "html", "jpg", "png", "gif", "lst", "JPG", "htm", "doc", "GIF", "JPE", "b64", "BIN",
        "Jpg", "zip", "dat", "rar", "bmp", "jpe","jpeg", "gz", "PDF.html", "url", "ng", "spec.patch",
        "spec", "patch", "p7s", "am"
    ]
    checks = [
        "ai_check_count_images", "ai_check_count_urls", "ai_check_from_equals_reply_to",
        "ai_check_return_path_equals_from_or_tos", "ai_check_email_client_id"
    ]

    def __init__(self, peer, mail_from, rcpt_tos, email_msg):
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
        if self.get_parsed_from() is not None:
            split_parsed_from = self.get_parsed_from().split("@")
            self._sender_domain = None if len(split_parsed_from) != 2 else split_parsed_from[1]
        else:
            self._sender_domain = None

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
        return EmailEnvelope.get_parsed_email_address(value)

    def get_parsed_to_list(self):
        """
        This method returns the parsed 'To' header (just email addresses)

        :return: The list of parsed recipients
        """
        email_tos = self.email_msg.get("To")
        return None if email_tos is None \
            else [EmailEnvelope.get_parsed_email_address(to_parse) for to_parse in email_tos.split(",")]

    def get_parsed_return_path(self):
        """
        This method returns the parsed 'Return-Path' to header (just email address), if any

        :return: The parsed 'Return-Path' header. None if the email doesn't have it.
        """
        value = self.email_msg.get('Return-Path')
        return EmailEnvelope.get_parsed_email_address(value)

    @staticmethod
    def get_parsed_email_address(header_value):
        """
        This utility method parses 'From', 'To' and 'Return-Path' headers to only email format
        :param header_value: the header to be parsed
        :return: The parsed header
        """
        if header_value is not None and '@' in header_value:
            aux_list = header_value.split("<")
            list_length = len(aux_list)
            return aux_list[0] if list_length == 1 else aux_list[list_length - 1][:-1]
        return None

    def get_x_headers(self):
        """
        This method gets all X-headers from the email message
        :return: the X-headers in dictionary format
        """
        x_headers = []
        for header in self.email_msg:
            if "X-" in header:
                x_headers.append(header)
        return x_headers

    def get_dkim_params(self):
        """
        This method gets all DKIM parameters from the email message
        :return: the DKIM parameters in dictionary format
        """
        dkim_params = {}
        dkim_data = self.email_msg.get('DKIM-Signature')
        if dkim_data is not None:
            for to_parse in dkim_data.split(';'):
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
            dig_data[parsed[0]] = parsed[1] if len(parsed) > 1 else ''
        ip_ranges = re.findall("ip[4|6]:([^ ]+)", dig_data['v'])
        includes = re.findall("include:([^ ]+)", dig_data['v'])
        redirect = re.findall("redirect=([^ ]+)", dig_data['v'])
        if redirect:
            ip_ranges.extend(EmailEnvelope.get_all_domain_ip_ranges(redirect[0]))
        if includes:
            for include in includes:
                ip_ranges.extend(EmailEnvelope.get_all_domain_ip_ranges(include))
        return ip_ranges

    # AI Methods

    def get_content_type_frequencies(self):
        """
        This function reads all the existent types of content in a email

        :return: dictionary with all types of content and their number of appearances
        """
        content_types = dict()

        for type in EmailEnvelope.all_content_types:
            content_types.__setitem__(type, 0)

        for part in self.email_msg.walk():
            content_type = part.get_content_type()
            n = content_types.get(content_type)
            if n is None:
                n = 0
            n += 1
            content_types[content_type] = n
        return content_types

    def get_extension_frequencies(self):
        """
        This function reads all the existent extensions of files in a email

        :return: dictionary with all types of content and their number of appearances
        """
        extension_types = dict()

        for type in self.all_extension_types:
            extension_types.__setitem__(type, 0)

        for content in self.email_msg.walk():
            if content.get('Content-Disposition') is not None:
                filename = content.get_filename()
                for extension in EmailEnvelope.all_extension_types:
                    match = re.search(rf"\.{extension}$", str(filename))
                    # if match is found
                    if match:
                        n = extension_types.get(extension)
                        if n is None:
                            n = 0
                        n += 1
                        extension_types[extension] = n
        return extension_types

    def ai_matrix_for_email(self):
        """
        This method build the vector of characteristics of the email.
        This method calls each criteria function and obtains the result
        :return: vector of characteristics of the email
        """
        email_matrix = []

        for check in EmailEnvelope.checks:
            check_result = getattr(self, check)()
            email_matrix.append(check_result)

        email_content_types = self.get_content_type_frequencies()
        for content_type in self.all_content_types:
            email_matrix.append(email_content_types.get(content_type))

        email_extension_types = self.get_extension_frequencies()
        for extension_type in self.all_extension_types:
            email_matrix.append(email_extension_types.get(extension_type))

        return email_matrix

    def ai_check_count_urls(self):
        """
        Counter of urls appearances
        :return: number of urls
        """
        num_urls = 0
        for content in self.email_msg.get_payload():
            num_urls += len(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', str(content)))
        return num_urls

    def ai_check_count_images(self):
        """
        Counter of images appearances
        :return: number of images
        """
        num_img = 0
        for content in self.email_msg.get_payload():
            num_img += len(re.findall(r'https?://(?:[-\w.]|/|(?:%[\da-fA-F]{2}))+\.(?:jpg|jpeg|gif|png)', str(content)))
        return num_img

    def ai_check_email_client_id(self):
        """
        This method calculates the hash of the sender domain. In order to obtain a positive hash, the python hash
        is adjusted by doing the next operation: hash % ((sys.maxsize + 1) * 2)
        Then, the hash is shortened by dividing it by the prime number 1111118111111
        :return: hash of the sender domain.
        """
        email_client = self.get_sender_domain()
        if email_client is not None:
            hash = email_client.__hash__() % ((sys.maxsize + 1) * 2)
            return int(round(hash / 1111118111111))
        return 0

    def ai_check_return_path_equals_from_or_tos(self):
        """
        This method checks if header Return-Path is different of header From
        and header Return-Path is not in the header To
        :return: True of False
        """
        parsed_return_path = self.get_parsed_return_path()
        to_list = self.get_parsed_to_list()
        if parsed_return_path is not None and to_list is not None:
            return parsed_return_path != self.get_parsed_from() and parsed_return_path not in to_list
        return False

    def ai_check_from_equals_reply_to(self):
        """
        This method checks if header From equals to header Repply-To
        :return: True or false
        """
        to_parse = self.email_msg.get('Reply-To')
        parsed_reply_to = EmailEnvelope.get_parsed_email_address(to_parse)
        if parsed_reply_to is not None:
            return to_parse == self.get_parsed_from()
        return False
