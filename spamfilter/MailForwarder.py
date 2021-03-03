import smtplib
import threading as th
import multiprocessing as mp


class MailForwarder:
    _msgs_to_forward = None
    _forward_ip = None
    _forward_port = None

    def __init__(self, ip, port, n_threads=mp.cpu_count()):
        self._msgs_to_forward = mp.Queue()
        self._forward_ip = ip
        self._forward_port = port
        self._n_threads = n_threads
        for i in range(n_threads):
            worker = th.Thread(target=self._forward_msg,
                               args=(self._msgs_to_forward, self._forward_ip, self._forward_port))
            worker.start()

    def forward(self, msg):
        self._msgs_to_forward.put(msg)

    @staticmethod
    def _forward_msg(msgs, ip, port):
        server = smtplib.SMTP(ip, port)
        try:
            while True:
                msg = msgs.get()
                print(f"[ {th.current_thread().name} ] Forwarding message")
                server.sendmail(from_addr=msg["From"], to_addrs=msg["To"], msg=msg.as_string())
                print(f"[ {th.current_thread().name} ] Message forwarded")
        finally:
            server.quit()
