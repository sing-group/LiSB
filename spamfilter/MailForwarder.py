import smtplib
import threading as th
import multiprocessing as mp
import logging

from spamfilter.EmailEnvelope import EmailEnvelope


class MailForwarder:
    _msgs_to_forward: mp.Queue
    _forward_ip = None
    _forward_port = None

    def __init__(self, ip: str, port: int = 1025, n_threads: int = mp.cpu_count()):
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
            worker = th.Thread(target=MailForwarder.__forward_msg, name=f"Forwarder-{i}",
                               args=(self._msgs_to_forward, self._forward_ip, self._forward_port))
            worker.start()

    def forward(self, msg: EmailEnvelope):
        """
        This method adds an email message to the forwarding queue

        :param msg: the message to be forwarded
        """
        self._msgs_to_forward.put(msg)

    @staticmethod
    def __forward_msg(msgs: mp.Queue, ip: str, port: int):
        """
        This static method is executed by the worker threads in order to forward the email messages from the queue

        :param msgs: the queue in which the messages are stored
        :param ip: the IP of the server to forward emails to
        :param port: the port of the server to forward emails to
        """
        server = None
        try:
            server = smtplib.SMTP(ip, port)
            logging.info(f"[ {th.current_thread().name} ] Ready to forward to {(ip, port)}")
            while True:
                msg: EmailEnvelope = msgs.get()
                logging.info(f"[ {th.current_thread().name} ] Forwarding message")
                server.sendmail(from_addr=msg.mail_from, to_addrs=msg.rcpt_tos, msg=msg.email_msg.as_bytes())
                logging.info(f"[ {th.current_thread().name} ] Message forwarded")
        except TimeoutError as e:
            logging.error(f'\033[91m[ {th.current_thread().name} ] Timeout while connecting to remote server\033[0m')
        except smtplib.SMTPServerDisconnected as e:
            logging.error(f'\033[91m[ {th.current_thread().name} ] Remote server unexpectedly closed the connection\033[0m')
        except ConnectionRefusedError as e:
            logging.error(f'\033[91m[ {th.current_thread().name} ] Could not connect to remote server (conn. refused)\033[0m')
        except Exception as e:
            logging.error(f'\033[91m[ {th.current_thread().name} ] An unexpected error occurred: {e}\033[0m')
        finally:
            if server:
                server.quit()
