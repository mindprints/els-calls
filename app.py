import json
import os
from functools import wraps
from datetime import datetime, time as time_obj
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from bottle import Bottle, request, response, static_file

app = Bottle()

# --- Authentication ---
APP_USER = os.getenv("APP_USER", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "password")

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            response.status = 401
            return ''

        user, pwd = request.auth
        if user != APP_USER or pwd != APP_PASSWORD:
            response.status = 401
            return "Authentication failed."

        return f(*args, **kwargs)
    return decorated

# CORS middleware
@app.hook("after_request")
def enable_cors():
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization"
    )

# ... (rest of the app is unchanged)
