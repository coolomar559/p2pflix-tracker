#!/usr/bin/env python3
from api import app

SERVER_PORT = 42069
DEBUG = True

if __name__ == '__main__':
    app.run(port=SERVER_PORT, debug=True)
