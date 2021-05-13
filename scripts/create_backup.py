#!/etc/spamfilter/venv/bin/python3.7
import os
import sys
import tarfile
from datetime import datetime

from schema import Schema, Or, Optional, And, SchemaError

command_schema = Schema({
    Optional("--to-backup"): And([Or("conf", "data", "logs")], lambda l: 0 < len(l) <= 3),
    Optional("--s3-bucket"): [],
    Optional("--encrypted"): []
})


def do_backup(options):
    # Crate backups directory if necessary
    base_path = "/etc/spamfilter/"
    backups_path = "/etc/spamfilter/backups/"
    if not os.path.exists(backups_path):
        os.makedirs(backups_path)

    # Create local backup file of information specified by '--to-backup'
    to_backup = ['conf', 'data', 'logs'] if '--to-backup' not in options else options['--to-backup']
    backup_name = backups_path + "backup" + datetime.now().strftime("%Y%m%d%H%M%S") + ".tar.gz"
    with tarfile.open(backup_name, "w:gz") as tar:
        print(f"Creating backup file {backup_name}")
        for info in to_backup:
            path_and_info = os.path.join(base_path, info)
            if os.path.exists(path_and_info):
                print(f"Adding '{path_and_info}' to backup file")
                tar.add(path_and_info)
    return


if __name__ == '__main__':

    # Transform command options into dictionary
    options = {}
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i].split("=")
        option_name = arg[0]
        option_values = [] if len(arg) == 1 else arg[1].split(",")
        options[option_name] = option_values

    # Validate parsed command line and do backup if everything is correct
    try:
        validated = command_schema.validate(options)
        do_backup(validated)
    except SchemaError as e:
        print("Usage: create_backup.py [ --option1=val1,val2 ... ]")
        print("If no options, all the information will be stored unencrypted and locally.")
        print("Options:\n")
        print("\t--to-backup\tThis indicates which information is going to be backed up. The possible values can be:"
              "conf, data, and/or logs, hence backup up the respective information."
              "If not specified, everything is backed up.\n")
        print("\t--s3-bucket\tThe script will upload the backup to the S3 bucket specified in 'conf/backups.json'. "
              "If not specified, the backup will only be stored locally.\n")
        print("\t--encrypted\tThis determines whether the backup will be encrypted. "
              "If not specified, the backup won't be encrypted.\n")
