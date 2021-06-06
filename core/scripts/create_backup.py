#!/etc/spamfilter/venv/bin/python3.7
import json
import os
import sys

import boto3
import tarfile
from datetime import datetime

from schema import Schema, Optional, And, Or

from common_functions import encrypt_file

# BACKUPS SCHEMA
command_schema = Schema({
    Optional("--to-backup"): And([Or("conf", "data", "logs")], lambda l: 0 < len(l) <= 3),
    Optional("--s3"): [And(str, lambda bucket_str: len(bucket_str.split("/", maxsplit=1)) == 2)],
    Optional("--encrypted"): And(list, lambda l: len(l) == 0)
})


def create_backup(options):
    # Crate backups directory if necessary
    base_path = "/etc/spamfilter/"
    backups_path = "/etc/spamfilter/backups/"
    if not os.path.exists(backups_path):
        os.makedirs(backups_path)

    # Create GZ-compressed local TAR backup file of information specified by '--to-backup'
    to_backup = ['conf', 'data', 'logs'] if '--to-backup' not in options else options['--to-backup']
    backup_name = "backup" + datetime.now().strftime("%Y%m%d%H%M%S") + ".tar.gz"
    backup_file_path = backups_path + backup_name
    print("Creating backup...")
    backed_up = []
    with tarfile.open(backup_file_path, "w:gz") as tar:
        for info in to_backup:
            path_and_info = os.path.join(base_path, info)
            if os.path.exists(path_and_info):
                print(f"Adding '{path_and_info}' to backup file...")
                backed_up.append(info)
                tar.add(path_and_info)

    if '--encrypted' in options:
        # Encrypt file and remove unencrypted file
        key = encrypt_file(backup_file_path, backup_file_path + ".enc")
        print(f"Encrypting backup file with this key: {key} ")
        print(f"Please store it securely for decryption")
        os.remove(backup_file_path)
        backup_name += ".enc"
        backup_file_path += ".enc"

    print(f"Storing the backup file '{backup_name}' at '{backups_path}'")

    # Upload to s3 bucket if needed
    uploaded = False
    if '--s3' in options:
        s3_client = boto3.client('s3')
        try:
            for s3_bucket in options['--s3']:
                s3_params = s3_bucket.split("/", maxsplit=1)
                s3_bucket_name = s3_params[0]
                s3_file_path = s3_params[1] + backup_name
                s3_client.upload_file(backup_file_path, s3_bucket_name, s3_file_path)
                uploaded = True
                print(f"The backup file was successfully uploaded to '{s3_bucket}'")
        except Exception as e:
            print(f"An error occurred: {e.__class__.__name__} - {e}\n")

    # Add info to backups log file

    backups_log_path = '/etc/spamfilter/backups/backups_log.json'

    if os.path.exists(backups_log_path):
        with open(backups_log_path, 'r') as file:
            backups_log = json.load(file)
    else:
        backups_log = {}

    backups_log[backup_name] = {
        'backed-up': backed_up,
        'timestamp': datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
        'uploaded-to-s3': uploaded
    }

    with open(backups_log_path, 'w') as file:
        json.dump(backups_log, file, indent=4)


if __name__ == '__main__':

    try:
        # Parse command options
        n_args = len(sys.argv)
        options = {}
        for i in range(1, n_args):
            arg = sys.argv[i].split("=")
            options[arg[0]] = [] if len(arg) == 1 else arg[1].split(",")

        # Validate command options
        validated = command_schema.validate(options)

        # Do backup if everything is correct
        create_backup(validated)

    except Exception as e:
        print(f"An error occurred: {e.__class__.__name__} - {e}\n")
        print("Usage: create_backup.py [ --option1=val1,val2 ... ]")
        print("If options are not passed as parameters, everything will be backed up locally and without encryption.\n")
        print("Options:\n")
        print("\t--to-backup\tThis indicates which information is going to be backed up. The possible values can be: "
              "conf, data, and/or logs, hence backup up the respective information."
              "If not specified, everything is backed up.\n")
        print("\t--s3=[BUCKET_NAME/PATH]\tThe script will upload backup to the the specified S3 buckets. "
              "If not specified, the backup will only be stored locally. "
              "Remember that, for this options to work correctly, S3 Full access needs to be enabled.\n")
        print("\t--encrypted\tThe backup will be encrypted with 256-AES in CBC mode. "
              "If not specified, the backup won't be encrypted.\n")
        print("\t--help\tThis option shows all of the command options.")
