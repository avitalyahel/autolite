#!flask/bin/python

import json
import subprocess

from flask import Flask, jsonify

import server

app = Flask(__name__)

@app.route('/')
def index() -> str:
    return server.index()

@app.route('/tasks', methods=['GET'])
def tasks_html() -> str:
    return server.html_tasks()

@app.route('/tasks/<string:name>', methods=['GET'])
def task_html(name: str = '') -> str:
    return server.html_task(name)

@app.route('/systems', methods=['GET'])
def system_html(name: str = '') -> str:
    return server.html_systems()

@app.route('/systems/<string:name>', methods=['GET'])
def systems_html(name: str = '') -> str:
    return server.html_system(name)

# REST API

@app.route('/api/v1/tasks', methods=['GET'])
@app.route('/api/v1/tasks/<string:name>', methods=['GET'])
def get_tasks(name: str = '') -> str:
    return jsonify(server.get_tasks(name))

@app.route('/api/v1/systems', methods=['GET'])
@app.route('/api/v1/systems/<string:name>', methods=['GET'])
def get_systems(name: str = '') -> str:
    return jsonify(server.get_systems(name))


if __name__ == '__main__':
    server.set_root_url('/')
    app.run(debug=True, host='0.0.0.0', port=8080)

