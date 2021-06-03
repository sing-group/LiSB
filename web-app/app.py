import datetime
import os
import json
import sys
from collections import OrderedDict

from schema import SchemaError, Schema
from config import routes
from flask import Flask, render_template, request, redirect, flash, session, jsonify

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
                to_write = json.dumps(validated, indent=4)
                conf_file.write(to_write)
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
    # Get URL params
    date = request.args.get('date')
    time = request.args.get('time')
    severity = request.args.get('severity')
    module_and_thread = request.args.get('module_and_thread')
    msg = request.args.get('msg')

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
    sorted_past_logs = []
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
            sorted_past_logs.append((timestamp, parsed_log))

    sorted_past_logs.sort(key=lambda x: x[0], reverse=False)

    return render_template(
        "past_logs_monitor.html",
        past_logs=sorted_past_logs,
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


if __name__ == '__main__':
    # Append core module to path and import it
    sys.path.insert(1, routes['core'])
    import core

    # Run web app
    app.secret_key = os.urandom(24)
    app.run(debug=True)
