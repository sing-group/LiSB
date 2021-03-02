import smtpd
import email


class SpamFilter(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print('\nA NEW MESSAGE HAS BEEN RECEIVED\n')
        msg = email.message_from_bytes(data)
        print(msg)
        self.forward_message(msg)
        return

    def forward_message(self, msg):
        try:
            ip = self._remoteaddr[0]
            port = self._remoteaddr[1]
            print('\nForwarding message to (', ip, ':', port, ')')
            server = smtpd.SMTPServer(ip, port)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(e)
