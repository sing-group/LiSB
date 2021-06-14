import logging
import jsonpickle
from core.EmailEnvelope import EmailEnvelope
from core.filtering.filters.PastFilter import PastFilter
from typing import Sequence


class AIFilter(PastFilter):
    checks: Sequence[str] = ["get_count_urls", "get_count_images", "get_from_return_path", "get_from_reply_to",
                             "get_id_email_client"]
    all_content_types = ["text/html", "text/plain", "multipart/mixed", "application/octet-stream",
                         "multipart/alternative", "multipart/related", "image/jpeg", "image/gif", "message/rfc822",
                         "text/plain charset=us-ascii", "image/png", "text/x-vcard", "image/bmp",
                         "application/x-zip-compressed", "multipart/signed", "application/pgp-signature",
                         "text/enriched", "application/ms-tnef", "video/mng", "application/x-pkcs7-signature",
                         "multipart/report", "message/delivery-status", "text/rfc822-headers",
                         "application/x-java-applet", "application/x-patch"]
    all_extension_types = ["txt", "html", "jpg", "png", "gif", "lst", "JPG", "htm", "doc", "GIF", "JPE", "b64", "BIN",
                           "Jpg", "zip", "dat", "rar", "bmp", "jpe", "gz", "PDF.html", "url", "ng", "spec.patch",
                           "spec", "patch", "p7s", "am", "jpeg"]

    def set_initial_data(self, data):
        """
        This method initialize the data which was read from the respective model's file
        :param data: data read of the model's file
        """
        self.data = jsonpickle.decode(data)

    def filter(self, envelope: EmailEnvelope) -> bool:
        """
        This method return the classification of the email, if 1 is Spa,
        :param envelope: email
        :return: if 1 then is spam and return true, else false
        """
        email_params = envelope.ai_matrix_for_email()
        is_spam = True if self.data.predict([email_params]) == [1] else False
        if is_spam:
            logging.info(f"An AIFilter has detected the email as spam")
        return is_spam
