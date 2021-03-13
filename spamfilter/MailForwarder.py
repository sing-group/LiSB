import smtplib
import threading as th
import multiprocessing as mp
from typing import Sequence

from spamfilter.EmailEnvelope import EmailEnvelope


class MailForwarder:
    _msgs_to_forward: mp.Queue
    _forward_ip = None
    _forward_port = None

    def __init__(self, ip: str, port: int = 1, n_threads: int = mp.cpu_count()):
        """
        This method creates a multi-thread mail forwarder based on queues

        :param ip: the IP of the server to forward emails to
        :param port: the port of the server to forward emails to
        :param n_threads: the number of threads that will be created (number of CPUs by default)
        """
        self._msgs_to_forward = mp.Queue()
        self._forward_ip = ip
        self._forward_port = port
        self._n_threads = n_threads
        for i in range(n_threads):
            worker = th.Thread(target=self._forward_msg, name=f"Forwarder-{i}",
                               args=(self._msgs_to_forward, self._forward_ip, self._forward_port))
            worker.start()

    def forward(self, msg: EmailEnvelope):
        """
        This method adds an email message to the forwarding queue

        :param msg: the message to be forwarded
        """
        self._msgs_to_forward.put(msg)

    @staticmethod
    def _forward_msg(msgs: mp.Queue, ip: str, port: int):
        """
        This static method is executed by the worker threads in order to forward the email messages from the queue

        :param msgs: the queue in which the messages are stored
        :param ip: the IP of the server to forward emails to
        :param port: the port of the server to forward emails to
        """
        try:
            server = smtplib.SMTP(ip, port)
            print(f"[ {th.current_thread().name} ] Ready to forward")
            try:
                while True:
                    msg = msgs.get()
                    print(f"[ {th.current_thread().name} ] Forwarding message")
                    server.sendmail(from_addr=msg.mail_from, to_addrs=msg.rcpt_tos, msg=msg.email_msg)
                    print(f"[ {th.current_thread().name} ] Message forwarded")
            finally:
                server.quit()
        except TimeoutError as e:
            print(f'\033[91m[ {th.current_thread().name} ] Timeout while connecting to remote server\033[0m')
