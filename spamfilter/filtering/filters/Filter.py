from spamfilter.EmailEnvelope import EmailEnvelope


class Filter:

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        Base method for spam filtering

        :param envelope:  The email message to be filtered
        :return: True if the message is detected as spam, False if it passes the filter
        """
        raise NotImplementedError("This method needs to be implemented")

    @staticmethod
    def parse_from_and_to(header: str) -> str:
        aux_list = header.split("<")
        list_length = len(aux_list)
        return aux_list[0] if list_length == 1 else aux_list[list_length - 1][:-1]

    @staticmethod
    def get_domain(email:str):
        return email.split("@")[1]