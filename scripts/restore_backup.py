#!/etc/spamfilter/venv/bin/python3.7
import os
import sys
import boto3
import tarfile
from schema import Schema, Optional, And

from common_functions import decrypt_file

command_schema = Schema({
    "--to-restore": And(str, lambda backup_file: len(backup_file) > 0),
    Optional("--s3"): And(str, lambda bucket_str: len(bucket_str.split("/", maxsplit=1)) == 2),
    Optional("--decryption"): str
})


def load_backup(options):
    base_path = "/etc/spamfilter/"
    backups_path = "/etc/spamfilter/backups/"
    to_restore = options['--to-restore']
    to_restore_path = backups_path + to_restore

    # Download file from S3 bucket
    if '--s3' in options:
        s3_params = options['--s3']
        print(f"Dowloading '{to_restore}' from 's3://{s3_params}'")
        try:
            s3_client = boto3.client('s3')
            s3_params = s3_params.split("/", maxsplit=1)
            s3_bucket_name = s3_params[0]
            s3_file_path = s3_params[1] + to_restore
            s3_client.download_file(s3_bucket_name, s3_file_path, to_restore_path)
        except Exception as e:
            print(f"Error while uploading file to '{s3_bucket_name}': {e.__class__.__name__} - {e}")

    if not os.path.exists(to_restore_path):
        print(f"The specified backup file {to_restore} doesn't exist at {backups_path}")
    else:
        if to_restore.rsplit(".", 1)[1] == "enc":
            if '--decryption' in options:
                print("Decrypting backup file...")
                # Decrypt backup file
                private_key_file = options["--decryption"]
                decrypted_path = to_restore_path[:-4]
                decrypt_file(to_restore_path, decrypted_path, private_key_file)
                # Remove encrypted file
                os.remove(to_restore_path)
                to_restore_path = decrypted_path
                # Extract all files from backup
                print("The backup file has been restored")
                with tarfile.open(to_restore_path) as tar:
                    tar.extractall('/')
            else:
                print("The file is encrypted and no private key was specified")
        else:
            # Extract all files from backup
            print("The backup file has been restored")
            with tarfile.open(to_restore_path) as tar:
                tar.extractall('/')


if __name__ == '__main__':

    try:
        # Parse command options
        options = {}
        n_args = len(sys.argv)
        for i in range(1, n_args):
            arg = sys.argv[i].split("=")
            options[arg[0]] = None if len(arg) == 1 else arg[1]

        # Validate
        validated = command_schema.validate(options)

        # Do backup if everything is correct
        load_backup(validated)

    except Exception as e:
        print("Usage: load_backup.py --to-restore=BACKUP_FILE [ --option1=val1,val2 ... ]")
        print("If options are not passed as parameters they are read from the 'conf/backups.json' file.\n")
        print("Options:\n")
        print("\t--to-restore\tThe backup file to be restored.\n")
        print("\t--s3=BUCKET_NAME/PATH\tThe S3 bucket and path where to find the backup file. "
              "If not specified, the backup file will be looked up locally at '/etc/spamfilter/backups/'. "
              "Remember that, for this options to work correctly, S3 Full access needs to be enabled.\n")
        print("\t--decryption=PRIVATE_KEY_FILE\tDecrypt the backup file with the private key stored at the passed file.")
        print("\t--help\tThis option shows all of the command options.")
