from spamfilter.EmailEnvelope import EmailEnvelope


class Filter:

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        Base method for spam filtering

        :param envelope:  The email message to be filtered
        :return: True if the message is detected as spam, False if it passes the filter
        """
        raise NotImplementedError("This method needs to be implemented")
