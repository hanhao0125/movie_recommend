from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from config import APRIORI_MODEL_PATH
import pickle as pkl
import logging
from flask.logging import default_handler


app = Flask(__name__)
app.config.from_object('config')
# logging config
fmt = '[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s][%(thread)d] - %(message)s'
fmt = logging.Formatter(fmt)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(fmt)

file_handler = logging.FileHandler('flask.log')
file_handler.setFormatter(fmt)
file_handler.setLevel(logging.INFO)
app.logger.removeHandler(default_handler)

app.logger.addHandler(stream_handler)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# mysql config
db = SQLAlchemy(app)
# redis config
redis_client = FlaskRedis(app)
# jinja and vue config
app.jinja_env.variable_start_string = '{{ '
app.jinja_env.variable_end_string = ' }}'
# login_manager config
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app=app)
# load apriori model
with open(APRIORI_MODEL_PATH, 'rb') as f:
    apriori_model = pkl.load(f)
