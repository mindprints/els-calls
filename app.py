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
            response.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'
            return ''

        user, pwd = request.auth
        if user != APP_USER or pwd != APP_PASSWORD:
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

# --- Configuration & Setup ---
SETTINGS_FILE = "settings.json"
AUDIO_DIR = "audio"

try:
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {
        "MIL_NUMBER": "",
        "FALLBACK_NUMBER": "",
        "ACTIVE_AUDIO_FILE": None,
        "SCHEDULE": [],
        "MAX_TURNS": 3,
        "LANG": "sv",
        "NAMED_NUMBERS": [],
    }

# ... (rest of the app)

# --- Static & UI Endpoints ---
@app.get("/")
@auth_required
def index():
    return static_file("index.html", root="/app")

@app.get("/audio/<filename>")
@auth_required
def serve_audio(filename: str):
    return static_file(filename, root=AUDIO_DIR, mimetype="audio/mpeg")

# --- Settings & Configuration API ---
@app.get("/settings")
@auth_required
def get_settings():
    return settings

@app.post("/settings")
@auth_required
def post_settings():
    # ... (function body remains the same)
    pass

# --- Schedule API ---
@app.post("/schedule")
@auth_required
def add_schedule_entry():
    # ... (function body remains the same)
    pass

@app.delete("/schedule/<index:int>")
@auth_required
def delete_schedule_entry(index):
    # ... (function body remains the same)
    pass

# --- Named Numbers API ---
@app.post("/named_numbers")
@auth_required
def add_named_number():
    # ... (function body remains the same)
    pass

@app.put("/named_numbers/<index:int>")
@auth_required
def update_named_number(index):
    # ... (function body remains the same)
    pass

@app.delete("/named_numbers/<index:int>")
@auth_required
def delete_named_number(index):
    # ... (function body remains the same)
    pass

# --- Audio File Management API ---
@app.get("/audio_files")
@auth_required
def list_audio_files():
    # ... (function body remains the same)
    pass

@app.post("/upload_audio")
@auth_required
def upload_audio():
    # ... (function body remains the same)
    pass

@app.delete("/audio/<filename>")
@auth_required
def delete_audio_file(filename: str):
    # ... (function body remains the same)
    pass

if __name__ == "__main__":
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
    app.run(host="0.0.0.0", port=8000, debug=True)
