#!/etc/spamfilter/venv/bin/python3.7
import json
import os
import sys
import boto3
import tarfile
from datetime import datetime
from schema import Schema, Or, Optional, And, SchemaError

command_schema = Schema({
    Optional("--to-backup"): And([Or("conf", "data", "logs")], lambda l: 0 < len(l) <= 3),
    Optional("--s3"): And([str, lambda bucket_str: len(bucket_str.split("/", maxsplit=1))]),
    Optional("--encryption"): []
})


def parse_args():
    """
    This function parses the arguments passed to the scripts. In case no arguments are passed, they are loaded from the 'conf/backups.json' file
    :return: the parsed arguments in dictionary format
    """
    n_args = len(sys.argv)
    if n_args == 1:
        # If not passed as parameters, they are read from the conf/backups.json file
        with open("conf/backups.json") as backups_conf_file:
            options = json.load(backups_conf_file)
        if not options:
            raise Exception("The options file needs to be configured")
    else:
        options = {}
        for i in range(1, n_args):
            arg = sys.argv[i].split("=")
            options[arg[0]] = [] if len(arg) == 1 else arg[1].split(",")
    return options


def do_backup(options):
    # Crate backups directory if necessary
    base_path = "/etc/spamfilter/"
    backups_path = "/etc/spamfilter/backups/"
    if not os.path.exists(backups_path):
        os.makedirs(backups_path)

    # Create local backup file of information specified by '--to-backup'
    to_backup = ['conf', 'data', 'logs'] if '--to-backup' not in options else options['--to-backup']
    backup_name = "backup" + datetime.now().strftime("%Y%m%d%H%M%S") + ".tar.gz"
    backup_file_path = backups_path + backup_name
    with tarfile.open(backup_file_path, "w:gz") as tar:
        print(f"Creating backup file '{backup_name}' at '{backups_path}'")
        for info in to_backup:
            path_and_info = os.path.join(base_path, info)
            if os.path.exists(path_and_info):
                print(f"Adding '{path_and_info}' to backup file")
                tar.add(path_and_info)

    # Upload to s3 bucket if needed
    if '--s3' in options:
        s3_client = boto3.client('s3')
        try:
            for s3_bucket in options['--s3']:
                s3_params = s3_bucket.split("/", maxsplit=1)
                s3_bucket_name = s3_params[0]
                s3_file_path = s3_params[1] + backup_name
                s3_client.upload_file(backup_file_path, s3_bucket_name, s3_file_path)
                print(f"The backup file was successfully uploaded to '{s3_bucket}'")
        except Exception as e:
            print(f"Error while uploading file to '{s3_bucket}': {e.__class__.__name__} - {e}")


if __name__ == '__main__':

    try:
        # Parse command options
        options = parse_args()
        # Validate
        validated = command_schema.validate(options)
        # Do backup if everything is correct
        do_backup(validated)
    except Exception as e:
        print("Usage: create_backup.py [ --option1=val1,val2 ... ]")
        print("If options are not passed as parameters they are read from the 'conf/backups.json' file.\n")
        print("Options:\n")
        print("\t--to-backup\tThis indicates which information is going to be backed up. The possible values can be: "
              "conf, data, and/or logs, hence backup up the respective information."
              "If not specified, everything is backed up.\n")
        print(
            "\t--s3=bucket_name/path\tThe script will upload the backup to the S3 bucket specified in 'conf/backups.json'. "
            "If not specified, the backup will only be stored locally. AWS S3 Full access needs to be enabled.\n")
        print("\t--encryption\tThis determines how the backup will be encrypted. "
              "If not specified, the backup won't be encrypted.\n")
        print("\t--help\tThis option shows all of the command options.")
