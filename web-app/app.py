import sys
from flask import Flask, render_template, request, redirect
import os

from config import routes

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    conf_files = [file[:-5] for file in os.listdir(routes['conf'])]
    return render_template('index.html', config_files=conf_files)


@app.route('/conf/<filename>', methods=['GET', 'POST'])
def edit_conf_file(filename):
    file_path = os.path.join(routes['conf'], filename) + ".json"
    if request.method == 'GET':
        with open(file_path, 'r') as conf_file:
            conf_file_contents = conf_file.read()
        return render_template('edit_conf_file.html', filename=filename, conf_file_contents=conf_file_contents)
    else:
        updated_file_contents = request.form.get('updated-file-contents')

        with open(file_path, 'w') as conf_file:
            conf_file.write(updated_file_contents)
        return redirect(f"/conf/{filename}")


if __name__ == '__main__':
    sys.path.insert(1, routes['code'])
    app.run(debug=True)
