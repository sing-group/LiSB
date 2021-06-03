import datetime
import os
import json
import re
import sys
import subprocess
from schema import SchemaError
from config import routes
from flask import Flask, render_template, request, redirect, flash, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    conf_files = [file[:-5] for file in os.listdir(routes['conf'])]
    return render_template('index.html', config_files=conf_files)


@app.route('/conf/<filename>', methods=['GET', 'POST'])
def edit_conf_file(filename):
    # Get file path
    file_path = os.path.join(routes['conf'], filename) + ".json"

    # If GET, then retrieve file contents and simply show editor
    if request.method == 'GET':
        with open(file_path, 'r') as conf_file:
            conf_file_contents = conf_file.read()
        return render_template('edit_conf_file.html', filename=filename, conf_file_contents=conf_file_contents)

    # If POST, then validate updated file contents and store them. Then, redirect.
    # If the updated contents don't pass the validation, then inform about it.
    else:
        try:
            updated_file_contents = json.loads(request.form.get('updated-file-contents'))
            validation_schema = core.configuration.get_config_schema(filename)
            validated = validation_schema.validate(updated_file_contents)
            if validation_schema.ignore_extra_keys:
                validated = updated_file_contents
            with open(file_path, 'w') as conf_file:
                json.dump(validated, conf_file, indent=4)
            flash(f"The '{filename}' settings file was correctly updated.")
        except SchemaError as e:
            flash(f"There was an error: {e}")
            flash("Changes couldn't be applied.")
        return redirect(f"/conf/{filename}")


@app.route('/monitor/real-time/<int:timestamp>')
def real_time_monitor(timestamp):
    # Convert JS timestamp to datetime
    last_log_timestamp = datetime.datetime.fromtimestamp(timestamp / 1000)

    # Open current log file if any and get logs whose timestamp is greater than the one received
    response = []
    log_path = os.path.join(routes['logs'], "log")
    if os.path.exists(log_path):
        # Open current log file into lines array
        with open(log_path, 'r') as log_file:
            log_file_lines = log_file.readlines()
        # Iterate over log lines and get the most recent ones
        for log in log_file_lines:
            log_timestamp_str = log[2:25]
            log_timestamp = datetime.datetime.strptime(log_timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            if last_log_timestamp < log_timestamp:
                response.append(log)

    # Return response as JSON-like object
    return jsonify(response)


@app.route('/monitor/past-logs', methods=["GET"])
def past_logs_monitor():
    past_logs = []

    # If logs directory exists, then get logs if any
    if os.path.exists(routes['logs']):

        # Get all logs filenames and order them by timestamp
        unsorted_past_logs = []
        for log_file in os.listdir(routes['logs']):
            # Read by lines
            file_path = os.path.join(routes['logs'], log_file)
            with open(file_path, 'r') as file:
                log_file_lines = file.readlines()
            # Append logs
            unsorted_past_logs.extend(log_file_lines)

        # Get timestamps, parse logs and sort by  timestamp
        for log in unsorted_past_logs:

            # Get timestamp
            timestamp = datetime.datetime.strptime(log[2:25], "%Y-%m-%d %H:%M:%S,%f").timestamp()

            # Parse log
            log_elements = [e.replace('[', '').strip() for e in log.split("]")]
            log_datetime = log_elements[0].split(' ')
            log_date = log_datetime[0].split('-')
            log_time = log_datetime[1].split(":")
            parsed_log = {
                "year": log_date[0],
                "month": log_date[1],
                "day": log_date[2],
                "hour": log_time[0],
                "minute": log_time[1],
                "severity": log_elements[1],
                "module_and_thread": log_elements[2],
                "msg": log_elements[3]
            }

            # Append if necessary
            is_appended = True
            for k, v in parsed_log.items():
                # Get value from URL
                request_arg_value = request.args.get(k)
                is_appended = is_appended and (
                        request_arg_value == v or request_arg_value == "" or request_arg_value is None
                )
            if is_appended:
                past_logs.append((timestamp, parsed_log))

        # Sort logs by timestamp
        past_logs.sort(key=lambda x: x[0], reverse=False)

    return render_template(
        "past_logs_monitor.html",
        past_logs=past_logs,
        attributes={
            "year": "Year",
            "month": "Month",
            "day": "Day",
            "hour": "Hour",
            "minute": "Minute",
            "severity": "Severity",
            "module_and_thread": "Module & Thread",
            "msg": "Message"
        }
    )


@app.route('/backups/list', methods=["GET"])
def list_backups():
    # Get all backup file names if any and pass them to template
    backup_files = [] if not os.path.exists(routes['backups']) \
        else [backup_file for backup_file in os.listdir(routes['backups']) if backup_file != "backups_log.json"]

    # Get backups log from file
    bacukps_log_path = os.path.join(routes['backups'], 'backups_log.json')
    if os.path.exists(bacukps_log_path):
        with open(bacukps_log_path, 'r') as file:
            backups_log = json.load(file)
    else:
        backups_log = {}

    return render_template('list_backups.html', backup_files=backup_files, backups_log=backups_log)


@app.route('/backups/create', methods=["POST", "GET"])
def create_backups():
    if request.method == 'GET':
        return render_template('create_backups.html')
    else:

        # Parse form fields into command line and execute.
        # If there are errors, and go back to form page and inform with
        command_line = [os.path.join(routes['scripts'], "create_backup.py")]

        # Get files to backup
        to_backup = [info for info in ['logs', 'data', 'conf'] if request.form.get(info) == 'on']
        error = False
        if not to_backup:
            error = True
            flash("Please select which files you want to backup")
        else:
            command_line.append(f"--to-backup={','.join(to_backup)}")

        # Get S3 options
        if request.form.get('s3-upload') == 'yes':
            s3_bucket_name = request.form.get('s3-bucket-name')
            s3_bucket_path = request.form.get('s3-bucket-path')
            if s3_bucket_name == "" or s3_bucket_path == "":
                error = True
                flash("Please, enter a valid S3 bucket configuration")
            else:
                s3 = os.path.join(s3_bucket_name, s3_bucket_path)
                command_line.append(f"--s3={s3}")

        # Get encryption options
        if request.form.get('encrypted') == "yes":
            command_line.append("--encrypted")

        if error:
            return render_template('create_backups.html')
        else:

            # Execute command and get output
            result = subprocess.run(command_line, stdout=subprocess.PIPE).stdout.decode('utf-8')

            # Get backup name from output and flash it
            name_regex = re.compile("file '.*' at")
            name = name_regex.search(result).group(0)[5:-3]
            flash(f"A new backup file has been created: {name}")

            # If encrypted, get encryption key from output and flash it
            if request.form.get('encrypted') == "yes":
                key_regex = re.compile("b'.*'")
                key = key_regex.search(result).group(0)
                flash(f"Used encryption key: {key}. Please store it securely for decryption.")

            return redirect('/backups/list')


if __name__ == '__main__':
    # Append core module to path and import it
    sys.path.insert(1, routes['base'])
    import core

    # Run web app
    app.secret_key = os.urandom(24)
    app.run(debug=True)
