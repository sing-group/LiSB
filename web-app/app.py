import datetime
import os
import json
import re
import signal
import subprocess
import sys

import psutil

from schema import SchemaError
from config import routes
from flask import Flask, render_template, request, redirect, flash, jsonify, abort
from flask_paginate import Pagination, get_page_parameter

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/', methods=['GET'])
def index():
    # Check if SMTP server is running and pass sender status
    is_running = check_running_process('launcher.py')
    server_status = {
        "msg": "RUNNING",
        "msg-class": "running",
        "ajax": "do_stop_ajax_query()",
        "btn-txt": "Stop Server",
        "btn-class": "btn-danger"
    } if is_running else {
        "msg": "NOT RUNNING",
        "msg-class": "not-running",
        "ajax": "do_start_ajax_query()",
        "btn-txt": "Start Server",
        "btn-class": "btn-success"
    }
    return render_template(
        'monitor/monitor_server_status.html',
        server_status=server_status
    )


def check_running_process(process):
    for proc in psutil.process_iter():
        if process == proc.name() and proc.status() != "zombie":
            return proc.pid
    return False


@app.route('/ajax/start', methods=['POST'])
def start_server():
    # Run launcher if not yet launched and redirect to control panel
    is_running = check_running_process('launcher.py')
    if not is_running:
        subprocess.Popen(
            ['./launcher.py', '1>/dev/null', '2>/dev/null', '&'],
            cwd=routes['base'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({"msg": "The server was started"}), 200
    else:
        return jsonify({"msg": "The server was already running"}), 400


@app.route('/ajax/stop', methods=['POST'])
def stop_server():
    # Stop server and redirect to control panel
    spamfilter_pid = check_running_process('launcher.py')
    if spamfilter_pid:
        os.kill(spamfilter_pid, signal.SIGTERM)
        running = True
        while running:
            running = check_running_process('launcher.py')
        return jsonify({"msg": "The server was stopped"}), 200
    else:
        return jsonify({"msg": "The server is not running"}), 400


@app.route('/conf/<filename>', methods=['GET', 'POST'])
def edit_conf_file(filename):
    # Get file path
    file_path = os.path.join(routes['conf'], filename) + ".json"

    # If GET, then retrieve file contents and simply show editor
    if request.method == 'GET':
        with open(file_path, 'r') as conf_file:
            conf_file_contents = conf_file.read()
        return render_template('config_edit.html', filename=filename, conf_file_contents=conf_file_contents)

    # If POST, then validate updated file contents and store them. Then, redirect.
    # If the updated contents don't pass the validation, then inform about it.
    else:
        try:
            # Import configuration module
            sys.path.insert(1, routes['base'])
            from core import configuration
            # Validate and update if correct
            updated_file_contents = json.loads(request.form.get('updated-file-contents'))
            validation_schema = configuration.get_config_schema(filename)
            validated = validation_schema.validate(updated_file_contents)
            if validation_schema.ignore_extra_keys:
                validated = updated_file_contents
            with open(file_path, 'w') as conf_file:
                json.dump(validated, conf_file, indent=4)
            flash(f"The '{filename}' settings file was correctly updated.")
        except SchemaError as e:
            flash(f"Changes couldn't be applied since there was an error: {e}.", "error")
        return redirect(f"/conf/{filename}")


@app.route('/ajax/real-time-monitor/<int:timestamp>')
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
                parsed_log = [e.replace('[', '').strip() for e in log.split("]")]
                response.append({
                    "timestamp": parsed_log[0],
                    "level": parsed_log[1],
                    "module_and_thread": parsed_log[2],
                    "msg": parsed_log[3]
                })

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
                        request_arg_value == v or not request_arg_value
                )
            if is_appended:
                past_logs.append((timestamp, parsed_log))

        # Sort logs by timestamp
        past_logs.sort(key=lambda x: x[0], reverse=False)

    # Paginate
    search = False
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10
    offset = (page - 1) * per_page

    pagination = Pagination(page=page, css_framework='bootstrap', bs_version=4, total=len(past_logs), per_page=10,
                            search=search, record_name='past logs')

    return render_template(
        "monitor/monitor_past_logs.html",
        past_logs=past_logs[offset:offset + per_page],
        pagination=pagination,
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
    # Get backups log from file
    backups_log_path = os.path.join(routes['backups'], 'backups_log.json')
    if os.path.exists(backups_log_path):
        with open(backups_log_path, 'r') as file:
            backups_log = json.load(file)
    else:
        backups_log = {}

    return render_template('backups/backups_list.html', backups_log=backups_log)


@app.route('/backups/create', methods=["POST", "GET"])
def create_backups():
    if request.method == 'GET':
        return render_template('backups/backups_create.html')
    else:

        # Parse form fields into command line and execute.
        # If there are errors, and go back to form page and inform with
        command_line = [os.path.join(routes['scripts'], "create_backup.py")]

        # Get files to backup
        to_backup = [info for info in ['logs', 'data', 'conf'] if request.form.get(info) == 'on']
        error = False
        if not to_backup:
            error = True
            flash("Please select which files you want to backup.", "error")
        else:
            command_line.append(f"--to-backup={','.join(to_backup)}")

        # Get S3 options
        if request.form.get('s3-upload') == 'yes':
            s3_bucket_name = request.form.get('s3-bucket-name')
            s3_bucket_path = request.form.get('s3-bucket-path')
            if not s3_bucket_name or not s3_bucket_path:
                error = True
                flash("Please, enter a valid S3 bucket configuration.", "error")
            else:
                s3 = os.path.join(s3_bucket_name, s3_bucket_path)
                command_line.append(f"--s3={s3}")

        # Get encryption options
        if request.form.get('encrypted') == "yes":
            command_line.append("--encrypted")

        if error:
            return render_template('backups/backups_create.html')
        else:

            # Execute command and get output
            result = subprocess.run(command_line, stdout=subprocess.PIPE).stdout.decode('utf-8')

            # Get backup name from output and flash it
            name_regex = re.compile("file '.*' at")
            name = name_regex.search(result).group(0)[5:-3]
            flash(f"A new backup file has been created: {name}.")

            # If encrypted, get encryption key from output and flash it
            if request.form.get('encrypted') == "yes":
                key_regex = re.compile("b'.*'")
                key = key_regex.search(result).group(0)
                flash(f"Used encryption key: {key}. Please store it securely for decryption.")

            # Check if errors
            errors_regex = re.compile("An error occurred: .*")
            errors = re.findall(errors_regex, result)
            if len(errors) > 0:
                for error in errors:
                    flash(error, "error")

            return redirect('/backups/list')


@app.route('/backups/restore/local', methods=["POST"])
def restore_local_backups():
    to_restore = request.form.get('to-restore')
    if not to_restore:
        # Return Bad Request code
        abort(400)
    else:
        backup_path = os.path.join(routes['backups'], to_restore)
        if os.path.exists(backup_path):
            # Parse command line
            command_line = [os.path.join(routes['scripts'], "restore_backup.py"), f"--to-restore={to_restore}"]
            decryption_key = request.form.get('decryption-key')
            if decryption_key is not None:
                command_line.append(f"--decryption-key={decryption_key}")
            # Execute command
            result = subprocess.run(command_line, stdout=subprocess.PIPE).stdout.decode('utf-8')

            # Check if errors
            errors_regex = re.compile("An error occurred: .*")
            errors = re.findall(errors_regex, result)
            if len(errors) > 0:
                for error in errors:
                    flash(error, "error")
            else:
                flash(f"The '{to_restore}' backup file was properly restored.")

            # Redirect to backups list
            return redirect('/backups/list')
        else:
            # Return Not Found code
            abort(404)


@app.route('/backups/restore/s3', methods=["GET", "POST"])
def restore_s3_backups():
    if request.method == "GET":
        return render_template("backups/backups_restore_s3.html")
    else:

        # Check if errors and redirect wit verbose if any; else parse
        error = False

        to_restore = request.form.get('to-restore')
        if not to_restore:
            error = True
            flash("Please, enter a valid backup file.", "error")

        s3_bucket_name = request.form.get('s3-bucket-name')
        s3_bucket_path = request.form.get('s3-bucket-path')
        if not s3_bucket_name or not s3_bucket_path:
            error = True
            flash("Please, enter a valid S3 bucket configuration.", "error")

        if error:
            return redirect('/backups/restore/s3')
        else:

            # Parse command line
            command_line = [os.path.join(routes['scripts'], "restore_backup.py"), f"--to-restore={to_restore}",
                            f"--s3={os.path.join(s3_bucket_name, s3_bucket_path)}"]

            decryption_key = request.form.get('decryption-key')
            if decryption_key is not None:
                command_line.append(f"--decryption-key={decryption_key}")

            # Execute command
            result = subprocess.run(command_line, stdout=subprocess.PIPE).stdout.decode('utf-8')

            # Check if errors in command execution
            errors_regex = re.compile("An error occurred: .*")
            errors = re.findall(errors_regex, result)
            if len(errors) > 0:
                for error in errors:
                    flash(error, "error")
                return redirect('/backups/restore/s3')
            else:
                flash(f"The '{to_restore}' backup file was properly restored.")

            # Redirect to backups list

            return redirect('/backups/list')


@app.route('/backups/delete', methods=["POST"])
def delete_backups():
    to_delete = request.form.get('to-delete')
    if not to_delete:
        # Return Bad Request code
        abort(400)
    else:
        backup_path = os.path.join(routes['backups'], to_delete)
        if os.path.exists(backup_path):
            # Remove file and flash verbose
            os.remove(backup_path)
            flash(f"The '{to_delete}' backup file has been deleted.")
            # Read logs file
            backups_log_path = os.path.join(routes['backups'], 'backups_log.json')
            with open(backups_log_path, 'r') as file:
                logs = json.load(file)
            # Delete from logs
            logs.pop(to_delete, None)
            # Update logs file
            with open(backups_log_path, 'w') as file:
                json.dump(logs, file, indent=4)
            return redirect('/backups/list')
        else:
            # Return Not Found code
            abort(404)


# CONTEXT PROCESSOR THAT PASSES THE CONFIG FILES TO ALL TEMPLATES

@app.context_processor
def inject_config_files():
    return dict(config_files=[file[:-5] for file in os.listdir(routes['conf'])])


# ERROR HANDLERS

@app.errorhandler(400)
def page_not_found(e):
    return render_template('errors/400.html'), 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500
