import json
import os
from datetime import datetime, time

from bottle import Bottle, request, response, static_file

app = Bottle()

# --- Configuration & Setup ---
SETTINGS_FILE = "/app/settings.json"
AUDIO_DIR = "/app/audio"

# Global settings dictionary, loaded from file
try:
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
except FileNotFoundError:
    # Default settings if file doesn't exist
    settings = {
        "MIL_NUMBER": "",
        "FALLBACK_NUMBER": "",
        "ACTIVE_AUDIO_FILE": None,
        "SCHEDULE": [],
    }

# Ensure SCHEDULE key exists for backward compatibility
settings.setdefault("SCHEDULE", [])


def _save_settings():
    """Helper function to save the current settings to file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def _get_active_audio():
    """
    Determines the correct audio file to play based on the schedule.
    Returns the filename of the audio to play, or None if no audio should be played.
    """
    # Use UTC for server-side time comparison
    now = datetime.utcnow().time()

    # Check for an active scheduled item
    for slot in settings.get("SCHEDULE", []):
        try:
            start_time = time.fromisoformat(slot["start_time"])
            end_time = time.fromisoformat(slot["end_time"])

            # Handle overnight schedules (e.g., 22:00 to 02:00)
            if start_time <= end_time:
                # Normal same-day schedule
                if start_time <= now < end_time:
                    return slot["audio_file"]
            else:
                # Overnight schedule (spans across midnight)
                if now >= start_time or now < end_time:
                    return slot["audio_file"]
        except (ValueError, KeyError) as e:
            print(f"Skipping invalid schedule slot: {slot}. Error: {e}")
            continue

    # If no schedule matches, return the default active audio file
    return settings.get("ACTIVE_AUDIO_FILE")


# --- Static & UI Endpoints ---
@app.get("/")
def index():
    return static_file("index.html", root="/app")


@app.get("/audio/<filename>")
def serve_audio(filename: str):
    return static_file(filename, root=AUDIO_DIR, mimetype="audio/mpeg")


# --- Core 46elks API ---
@app.post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")
    print(f"from={from_number} mil={settings.get('MIL_NUMBER')}")

    if from_number == settings.get("MIL_NUMBER"):
        # Determine which audio to play based on schedule or default
        active_audio = _get_active_audio()

        if active_audio:
            # Security check: ensure file still exists before instructing a play
            if os.path.isfile(os.path.join(AUDIO_DIR, active_audio)):
                audio_url = f"https://calls.mtup.xyz/audio/{active_audio}"
                return {"play": audio_url}

        # If no scheduled or default audio, or if file is missing, hang up.
        return {"hangup": ""}

    # For any other number, connect to fallback
    return {"connect": settings.get("FALLBACK_NUMBER", "")}


# --- Settings & Configuration API ---
@app.get("/settings")
def get_settings():
    """Return current settings, including schedule."""
    return settings


@app.post("/settings")
def post_settings():
    """Update and save general settings (MIL, Fallback, default audio)."""
    new_data = request.json
    if (
        new_data
        and "MIL_NUMBER" in new_data
        and "FALLBACK_NUMBER" in new_data
        and "ACTIVE_AUDIO_FILE" in new_data
    ):
        settings["MIL_NUMBER"] = new_data["MIL_NUMBER"]
        settings["FALLBACK_NUMBER"] = new_data["FALLBACK_NUMBER"]

        selected_file = new_data["ACTIVE_AUDIO_FILE"]
        if selected_file is None:
            settings["ACTIVE_AUDIO_FILE"] = None
        else:
            audio_file_path = os.path.join(AUDIO_DIR, selected_file)
            if os.path.isfile(audio_file_path):
                settings["ACTIVE_AUDIO_FILE"] = selected_file
            else:
                return {
                    "status": "error",
                    "message": "Invalid default audio file.",
                }, 400

        _save_settings()
        return {"status": "success", "settings": settings}

    return {"status": "error", "message": "Invalid payload"}, 400


# --- Schedule API ---
@app.post("/schedule")
def add_schedule_entry():
    """Add a new time slot to the schedule."""
    data = request.json
    if not data or not all(k in data for k in ["audio_file", "start_time", "end_time"]):
        return {
            "status": "error",
            "message": "Invalid payload. Requires audio_file, start_time, and end_time.",
        }, 400

    # Validate audio file exists
    audio_file_path = os.path.join(AUDIO_DIR, data["audio_file"])
    if not os.path.isfile(audio_file_path):
        return {
            "status": "error",
            "message": "Scheduled audio file does not exist.",
        }, 400

    # Validate time format (HH:MM)
    try:
        time.fromisoformat(data["start_time"])
        time.fromisoformat(data["end_time"])
    except ValueError:
        return {"status": "error", "message": "Invalid time format. Use HH:MM."}, 400

    new_slot = {
        "audio_file": data["audio_file"],
        "start_time": data["start_time"],
        "end_time": data["end_time"],
    }

    settings["SCHEDULE"].append(new_slot)
    _save_settings()
    return {"status": "success", "schedule": settings["SCHEDULE"]}


@app.delete("/schedule/<index:int>")
def delete_schedule_entry(index):
    """Delete a schedule entry by its index."""
    try:
        if 0 <= index < len(settings["SCHEDULE"]):
            settings["SCHEDULE"].pop(index)
            _save_settings()
            return {"status": "success", "schedule": settings["SCHEDULE"]}
        else:
            return {"status": "error", "message": "Index out of bounds."}, 404
    except Exception as e:
        print(f"Error deleting schedule entry: {e}")
        return {"status": "error", "message": "Could not delete schedule entry."}, 500


# --- Audio File Management API ---
@app.get("/audio_files")
def list_audio_files():
    """Return a list of available audio files as a JSON array."""
    try:
        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)
        files = [
            f
            for f in os.listdir(AUDIO_DIR)
            if os.path.isfile(os.path.join(AUDIO_DIR, f)) and f.lower().endswith(".mp3")
        ]
        response.content_type = "application/json"
        return json.dumps(sorted(files))
    except Exception as e:
        print(f"Error listing audio files: {e}")
        response.status = 500
        return json.dumps({"status": "error", "message": "Could not list audio files."})


@app.post("/upload_audio")
def upload_audio():
    """Handle audio file uploads."""
    upload = request.files.get("audio_file")
    if not upload:
        return {"status": "error", "message": "No file provided."}, 400

    name, ext = os.path.splitext(upload.filename)
    if ext.lower() not in [".mp3"]:
        return {"status": "error", "message": "File must be an MP3."}, 400

    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    if not safe_name:
        return {"status": "error", "message": "Invalid filename characters."}, 400

    filename = f"{safe_name}{ext}"
    save_path = os.path.join(AUDIO_DIR, filename)

    if os.path.exists(save_path):
        return {"status": "error", "message": f"File '{filename}' already exists."}, 409

    try:
        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)
        upload.save(save_path)
        return {"status": "success", "filename": filename}
    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        return {"status": "error", "message": "Failed to save file."}, 500
