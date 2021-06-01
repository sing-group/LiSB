import os
import json
import time
import logging
import schedule
import threading as th
from os.path import join

from core.filtering.filters.PastFilter import PastFilter


class StorageManager:
    path: str

    def __init__(self, path, storing_frequency):
        """
        This method creates a new storage manager. It uses JSON format to store files.

        :param path: The path of the directory in which files will be stored to and loaded from
        (it will be created if it doesn't exist)
        :param storing_frequency: The frequency in seconds that define when the files are saved to disk
        """
        if not os.path.exists(path):
            os.makedirs(path)
        self.path = path
        self.storing_frequency = storing_frequency

    def store_data(self, filename, data):
        """
        This method stores the passed data to a file in the configured directory.

        :param filename: The filename of the file to store the data to (it will be created if it doesn't exist)
        :param data: The data to be stored as a JSON file
        """
        whole_filename = join(self.path, filename + '.json')
        logging.info(f"Storing {filename} data to '{whole_filename}'")
        with open(join(self.path, filename + '.json'), 'w') as json_file:
            json.dump(data, json_file, sort_keys=True)

    def load_data(self, filename) -> dict:
        """
        This method loads The data stored in the passed file.

        :param filename: The filename of the file to load the data from
        :return: If the file exists, it returns the data stored in it. If it doesn't, it returns an empty dictionary.
        """
        whole_filename = join(self.path, filename + '.json')
        logging.info(f"Retrieving data from '{whole_filename}'")
        if not os.path.exists(whole_filename):
            return {}
        else:
            with open(whole_filename) as json_file:
                data = json.load(json_file)
            return data

    def launch_storage_daemon(self, filters):
        """
        This method launches a daemon which periodically stores the filters' data to the respective files.

        The storing frequency is defined by 'storing_frequency'
        :param filters: The filters to get the data from
        """
        schedule.every(self.storing_frequency).seconds.do(StorageManager.store_all_data, self, filters)
        storage_daemon = th.Thread(target=StorageManager.__daemon_job, name="StorageDaemon")
        storage_daemon.start()

    @staticmethod
    def store_all_data(storage_mgr, filters):
        """
        This static method is the task that will be periodically performed by the storage daemon.

        :param storage_mgr: The StorageManager object
        :param filters: The filters to get the data from
        """
        for current_filter in filters:
            cls = type(current_filter)
            if issubclass(cls, PastFilter):
                to_store = current_filter.get_data()
                file_name = cls.__name__
                storage_mgr.store_data(file_name, to_store)

    @staticmethod
    def __daemon_job():
        """
        This static method is used by the storage daemon to wait for pending tasks to be ready to be executed
        """
        while True:
            schedule.run_pending()
            time.sleep(1)
