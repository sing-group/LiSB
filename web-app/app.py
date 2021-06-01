import datetime
import os
import json
import sys

from schema import SchemaError
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
            with open(file_path, 'w') as conf_file:
                to_write = json.dumps(validated)
                conf_file.write(to_write)
            flash(f"The '{filename}' settings file was correctly updated.")
        except SchemaError as e:
            flash(f"There was an error: {e}")
            flash("Changes couldn't be applied.")
        return redirect(f"/conf/{filename}")


@app.route('/monitor/real-time/<int:timestamp>')
def real_time_monitor(timestamp):
    last_log_timestamp = datetime.datetime.fromtimestamp(timestamp / 1000)
    response = []
    log_path = os.path.join(routes['logs'], "log")
    if os.path.exists(log_path):
        with open(log_path, 'r') as log_file:
            log_file_lines = log_file.readlines()
        for log in log_file_lines:
            log_timestamp_str = log[2:25]
            log_timestamp = datetime.datetime.strptime(log_timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            if last_log_timestamp < log_timestamp:
                response.append(log)
    return jsonify(response)


if __name__ == '__main__':
    # Append core module to path and import it
    sys.path.insert(1, routes['core'])
    import core

    # Run web app
    app.secret_key = os.urandom(24)
    app.run(debug=True)
