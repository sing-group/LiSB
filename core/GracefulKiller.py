import signal


class GracefulKiller:
    """
    This class is used for gracefully shutting down the server
    """
    kill_now = False

    def __init__(self):
        """
        This method returns a GracefulKiller object, which handles SIGINT and SIGTERM signals.
        """
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        """
        This method changes the sate of the kill_now flag, so that all of the processes that are listening to it can shutdown gracefully.
        """
        self.kill_now = True
