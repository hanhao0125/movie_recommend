from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
app.jinja_env.variable_start_string = '{{ '
app.jinja_env.variable_end_string = ' }}'