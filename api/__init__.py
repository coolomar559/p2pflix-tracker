from flask import Flask

app = Flask(__name__)

from api import routes  # noqa: E402, F401, I100, I202
