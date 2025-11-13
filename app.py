import json
import os
import time
from datetime import datetime, time
from pathlib import Path

import requests
from bottle import Bottle, request, response, static_file

# Import AI conversation module
from ai_conversation import conversation_manager

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
        "MAX_TURNS": 3,
        "LANG": "sv",
        "AI_REPLIES_ENABLED": True,
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


@app.get("/wip")
def wip_index():
    """Serve the work-in-progress HTML file."""
    return static_file("index_wip.html", root="/app")


@app.get("/audio/<filename>")
def serve_audio(filename: str):
    return static_file(filename, root=AUDIO_DIR, mimetype="audio/mpeg")


# --- AI Conversation Endpoints ---


@app.post("/recordings")
def handle_recording():
    """Process recordings from 46elks and generate AI responses"""
    call_id = request.forms.get("callid")
    audio_url = request.forms.get("wav")

    if not call_id or not audio_url:
        return {"status": "error", "message": "Missing callid or wav"}, 400

    try:
        # Process the conversation turn
        audio_path, response_text = conversation_manager.process_conversation_turn(
            audio_url, call_id, 1
        )

        if audio_path:
            filename = Path(audio_path).name
            print(f"✅ Generated response for call {call_id}: {response_text}")
            return {"status": "success", "filename": filename}
        else:
            print(f"❌ Failed to generate response for call {call_id}")
            return {"status": "error", "message": "Processing failed"}, 500

    except Exception as e:
        print(f"❌ Recording processing failed: {e}")
        return {"status": "error", "message": "Processing failed"}, 500


# --- Core 46elks API ---
@app.post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")
    call_id = request.forms.get("callid")
    mode = request.query.get("mode")

    print(
        f"from={from_number} mil={settings.get('MIL_NUMBER')} mode={mode} callid={call_id}"
    )

    # Non-MIL calls go to fallback
    if from_number != settings.get("MIL_NUMBER"):
        return {"connect": settings.get("FALLBACK_NUMBER", "")}

    # Check if AI replies are enabled
    if not settings.get("AI_REPLIES_ENABLED", True):
        # Fallback to original behavior
        active_audio = _get_active_audio()
        if active_audio and os.path.isfile(os.path.join(AUDIO_DIR, active_audio)):
            return {"play": f"https://calls.mtup.xyz/audio/{active_audio}"}
        return {"hangup": ""}

    # AI Conversation Flow
    base_url = "https://calls.mtup.xyz"
    max_turns = settings.get("MAX_TURNS", 3)

    if not mode:
        # Initial greeting
        return {
            "play": f"{base_url}/audio/hello.mp3",
            "skippable": False,
            "next": f"{base_url}/calls?mode=record1&callid={call_id}",
        }

    elif mode.startswith("record"):
        turn = int(mode.replace("record", ""))
        return {
            "record": f"{base_url}/recordings",
            "silencedetection": "yes",
            "timelimit": 12,
            "next": f"{base_url}/calls?mode=reply{turn}&callid={call_id}",
        }

    elif mode.startswith("reply"):
        turn = int(mode.replace("reply", ""))

        # Check if reply file exists
        reply_file = f"reply-{call_id}-{turn}.mp3"
        reply_path = os.path.join(AUDIO_DIR, reply_file)

        if os.path.exists(reply_path):
            response_data = {"play": f"{base_url}/audio/{reply_file}"}

            # Continue conversation if not at max turns
            if turn < max_turns:
                response_data["next"] = (
                    f"{base_url}/calls?mode=record{turn + 1}&callid={call_id}"
                )
            else:
                # Add closing message
                response_data["next"] = (
                    f"{base_url}/calls?mode=closing&callid={call_id}"
                )

            return response_data
        else:
            # Reply not ready yet, wait and retry
            return {
                "play": f"{base_url}/audio/waiting.mp3",
                "next": f"{base_url}/calls?mode=reply{turn}&callid={call_id}",
            }

    elif mode == "closing":
        return {
            "play": f"{base_url}/audio/goodbye.mp3"
            # No next - call ends here
        }

    # Fallback to original behavior
    active_audio = _get_active_audio()
    if active_audio and os.path.isfile(os.path.join(AUDIO_DIR, active_audio)):
        return {"play": f"{base_url}/audio/{active_audio}"}

    return {"hangup": ""}


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

        # Update AI settings if provided
        if "MAX_TURNS" in new_data:
            settings["MAX_TURNS"] = new_data["MAX_TURNS"]
        if "LANG" in new_data:
            settings["LANG"] = new_data["LANG"]
        if "AI_REPLIES_ENABLED" in new_data:
            settings["AI_REPLIES_ENABLED"] = new_data["AI_REPLIES_ENABLED"]

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

    # Validate time format (HH:MM) and check for conflicts
    try:
        new_start_t = time.fromisoformat(data["start_time"])
        new_end_t = time.fromisoformat(data["end_time"])
    except ValueError:
        return {"status": "error", "message": "Invalid time format. Use HH:MM."}, 400

    if new_start_t == new_end_t:
        return {
            "status": "error",
            "message": "Start and end times cannot be the same.",
        }, 400

    def get_ranges(start, end):
        if start < end:
            return [(start, end)]
        else:  # overnight
            return [(start, time.max), (time.min, end)]

    new_ranges = get_ranges(new_start_t, new_end_t)

    for existing_slot in settings.get("SCHEDULE", []):
        existing_start_t = time.fromisoformat(existing_slot["start_time"])
        existing_end_t = time.fromisoformat(existing_slot["end_time"])
        existing_ranges = get_ranges(existing_start_t, existing_end_t)

        for r1_start, r1_end in new_ranges:
            for r2_start, r2_end in existing_ranges:
                # Standard interval overlap check
                if r1_start < r2_end and r2_start < r1_end:
                    return {
                        "status": "error",
                        "message": f"Schedule conflict with existing slot: {existing_slot['audio_file']} ({existing_slot['start_time']}-{existing_slot['end_time']}).",
                    }, 409  # Conflict

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


@app.delete("/audio/<filename>")
def delete_audio_file(filename: str):
    """Delete an audio file, ensuring it's not in use."""
    # Basic security: prevent directory traversal.
    if ".." in filename or "/" in filename:
        return {"status": "error", "message": "Invalid filename."}, 400

    # Check if the file is set as the default active audio file.
    if settings.get("ACTIVE_AUDIO_FILE") == filename:
        return {
            "status": "error",
            "message": "Cannot delete file. It is set as the default active audio.",
        }, 409  # Conflict

    # Check if the file is used in any schedule.
    for slot in settings.get("SCHEDULE", []):
        if slot.get("audio_file") == filename:
            return {
                "status": "error",
                "message": f"Cannot delete file. It is used in a schedule ({slot['start_time']} - {slot['end_time']}).",
            }, 409

    try:
        file_path = os.path.join(AUDIO_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            return {"status": "success", "message": f"File '{filename}' deleted."}
        else:
            return {"status": "error", "message": "File not found."}, 404
    except Exception as e:
        print(f"Error deleting audio file '{filename}': {e}")
        return {
            "status": "error",
            "message": "Internal server error during deletion.",
        }, 500
