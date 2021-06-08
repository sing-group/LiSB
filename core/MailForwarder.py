import smtplib
import threading
import multiprocessing
import logging
import time
from queue import Empty

from core.EmailEnvelope import EmailEnvelope
from core.GracefulKiller import GracefulKiller


class MailForwarder:
    _msgs_to_forward: multiprocessing.Queue
    _forward_ip = None
    _forward_port = None
    _n_threads = None

    def __init__(self, ip: str, port: int = 1025, n_forwarder_threads: int = multiprocessing.cpu_count(),
                 killer: GracefulKiller = None):
        """
        This method creates a multi-thread mail forwarder based on queues

        :param ip: the IP of the server to forward emails to
        :param port: the port of the server to forward emails to
        :param n_forwarder_threads: the number of threads that will be created (number of CPUs by default)
        """
        self._msgs_to_forward = multiprocessing.Queue()
        self._forward_ip = ip
        self._forward_port = port
        self._n_threads = n_forwarder_threads

        for i in range(n_forwarder_threads):
            worker = threading.Thread(target=MailForwarder.__forward_msg, name=f"Forwarder-{i}",
                                      args=(self._msgs_to_forward, self._forward_ip, self._forward_port, killer))
            worker.start()

    def forward(self, msg: EmailEnvelope):
        """
        This method adds an email message to the forwarding queue

        :param msg: the message to be forwarded
        """
        self._msgs_to_forward.put(msg)

    @staticmethod
    def __forward_msg(msgs: multiprocessing.Queue, ip: str, port: int, killer: GracefulKiller):
        """
        This static method is executed by the worker threads in order to forward the email messages from the queue

        :param msgs: the queue in which the messages are stored
        :param ip: the IP of the server to forward emails to
        :param port: the port of the server to forward emails to
        """
        server = None
        msg: EmailEnvelope = None
        while not killer.kill_now or not msgs.empty():
            try:
                server = smtplib.SMTP(ip, port)
                logging.info(f"Ready to forward to {(ip, port)}")

                # Continue will not killed or if still has msgs to forward
                while not killer.kill_now or not msgs.empty():
                    try:
                        msg = msgs.get(timeout=5)
                        logging.info(f"Forwarding message")
                        server.sendmail(from_addr=msg.mail_from, to_addrs=msg.rcpt_tos, msg=msg.email_msg.as_bytes())
                        logging.info(f"Message forwarded")
                    except Empty:
                        logging.debu(f"Woken up but no emails to forward. Going back to sleep...")

                server.close()
            except TimeoutError as e:
                logging.error(f'Timeout while connecting to remote server')
            except smtplib.SMTPServerDisconnected as e:
                logging.error(f'Remote server unexpectedly closed the connection')
            except ConnectionRefusedError as e:
                logging.error(f'Could not connect to remote server (conn. refused)')
            except Exception as e:
                logging.error(f'An unexpected error occurred: {e}')
            finally:
                if msg is not None:
                    logging.info(f'Email has been put back in queue after error')
                    msgs.put(msg)
                    msg = None
                time.sleep(15)

        # After ending loop, inform
        logging.info("Closing connection and shutting down...")
