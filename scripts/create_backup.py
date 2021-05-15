#!/etc/spamfilter/venv/bin/python3.7
import os
import boto3
import tarfile
from datetime import datetime
from schema import Schema, Or, Optional, And

from common_functions import parse_args, encrypt_file

command_schema = Schema({
    Optional("--to-backup"): And([Or("conf", "data", "logs")], lambda l: 0 < len(l) <= 3),
    Optional("--s3"): And([str, lambda bucket_str: len(bucket_str.split("/", maxsplit=1))]),
    Optional("--encryption"): And(
        [str, lambda public_key_file: os.path.isfile(public_key_file)],
        lambda key_list: len(key_list) == 1
    )
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
    with tarfile.open(backup_file_path, "w:gz") as tar:
        for info in to_backup:
            path_and_info = os.path.join(base_path, info)
            if os.path.exists(path_and_info):
                print(f"Adding '{path_and_info}' to backup file...")
                tar.add(path_and_info)

    if '--encryption' in options:
        # Encrypt file and remove unencrypted file
        print("Encrypting backup file with your public SSH key")
        encrypt_file(backup_file_path, backup_file_path + ".enc", options['--encryption'][0])
        os.remove(backup_file_path)
        backup_name += ".enc"
        backup_file_path += ".enc"

    print(f"Storing the backup file '{backup_name}' at '{backups_path}'")

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
        options = parse_args("conf/backups.json")
        # Validate
        validated = command_schema.validate(options)
        # Do backup if everything is correct
        create_backup(validated)
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
