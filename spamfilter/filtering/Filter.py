from email.message import EmailMessage


class Filter:
    def filter(self, msg: EmailMessage) -> bool:
        """
        Base method for spam filtering
        :param msg:  The email message to be filtered
        :return: True if the message is detected as spam, False if it passes the filter
        """
        raise NotImplementedError("This method needs to be implemented")
