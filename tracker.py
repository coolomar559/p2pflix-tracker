#!/usr/bin/env python3
from pathlib import Path

from api import app, models

SERVER_PORT = 42069
DEBUG = True
DB_PATH = Path("tracker.db")

if __name__ == '__main__':
    models.load_database(DB_PATH)
    app.run(port=SERVER_PORT, debug=True)
