import json
import os
import time
from datetime import datetime, time as time_obj
from pathlib import Path
from typing import Dict, Optional, Tuple
from functools import wraps

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
            return '' # Return empty body for 401, no WWW-Authenticate header

        try:
            user, pwd = request.auth
            if user != APP_USER or pwd != APP_PASSWORD:
                response.status = 401
                return "Authentication failed."
        except (TypeError, ValueError):
            response.status = 401
            return "Invalid authentication."

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

# --- AI Conversation (omitted for brevity but is here) ---
class AIConversation:
    pass

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

settings.setdefault("SCHEDULE", [])
settings.setdefault("NAMED_NUMBERS", [])

def _save_settings():
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"❌ ERROR saving settings: {e}")


def _get_active_schedule_slot():
    now_utc = datetime.utcnow()
    current_time = now_utc.time()
    current_day = now_utc.weekday()

    for slot in settings.get("SCHEDULE", []):
        try:
            if current_day not in slot.get("days", []):
                continue
            start_time = datetime.strptime(slot["start_time"], "%H:%M").time()
            end_time = datetime.strptime(slot["end_time"], "%H:%M").time()
            if start_time <= end_time:
                if start_time <= current_time < end_time:
                    return slot
            else:
                if current_time >= start_time or current_time < end_time:
                    return slot
        except (ValueError, KeyError) as e:
            print(f"Skipping invalid schedule slot: {slot}. Error: {e}")
            continue
    return None

# --- Static & UI Endpoints ---
@app.get("/")
@auth_required
def index():
    return static_file("index.html", root="/app")

@app.get("/audio/<filename>")
@auth_required
def serve_audio(filename: str):
    return static_file(filename, root=AUDIO_DIR, mimetype="audio/mpeg")

# --- API Endpoints ---
@app.get("/settings")
@auth_required
def get_settings():
    return settings

@app.post("/settings")
@auth_required
def post_settings():
    new_data = request.json
    if not new_data: return {"status": "error", "message": "No data provided."}, 400
    for key in ["MIL_NUMBER", "FALLBACK_NUMBER", "MAX_TURNS", "LANG", "ACTIVE_AUDIO_FILE"]:
        if key in new_data:
            settings[key] = new_data[key]
    _save_settings()
    return {"status": "success", "settings": settings}

@app.post("/schedule")
@auth_required
def add_schedule_entry():
    data = request.json
    # ... (Full validation and logic from before)
    settings["SCHEDULE"].append(data)
    _save_settings()
    return {"status": "success", "schedule": settings["SCHEDULE"]}

@app.delete("/schedule/<index:int>")
@auth_required
def delete_schedule_entry(index):
    # ... (Full logic from before)
    settings["SCHEDULE"].pop(index)
    _save_settings()
    return {"status": "success", "schedule": settings["SCHEDULE"]}

@app.post("/named_numbers")
@auth_required
def add_named_number():
    data = request.json
    # ... (Full validation logic from before)
    settings["NAMED_NUMBERS"].append({"name": data["name"], "number": data["number"]})
    _save_settings()
    return {"status": "success", "named_numbers": settings["NAMED_NUMBERS"]}

@app.delete("/named_numbers/<index:int>")
@auth_required
def delete_named_number(index):
    # ... (Full logic from before)
    settings["NAMED_NUMBERS"].pop(index)
    _save_settings()
    return {"status": "success", "named_numbers": settings["NAMED_NUMBERS"]}

@app.get("/audio_files")
@auth_required
def list_audio_files():
    files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
    return json.dumps(sorted(files))

@app.post("/upload_audio")
@auth_required
def upload_audio():
    # ... (Full logic from before)
    return {"status": "success"}

@app.delete("/audio/<filename>")
@auth_required
def delete_audio_file(filename: str):
    # ... (Full logic from before)
    return {"status": "success"}

# --- 46elks Core API (unchanged) ---
@app.post("/calls")
def calls():
    pass

if __name__ == "__main__":
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
    app.run(host="0.0.0.0", port=8000, debug=True)
