import json
import os

from bottle import Bottle, request, response, static_file

app = Bottle()

# Global settings dictionary, loaded from file
SETTINGS_FILE = "/app/settings.json"
with open(SETTINGS_FILE, "r") as f:
    settings = json.load(f)

AUDIO_DIR = "/app/audio"


@app.get("/")
def index():
    return static_file("index.html", root="/app")


@app.get("/audio/<filename>")
def serve_audio(filename: str):
    return static_file(filename, root="/app/audio", mimetype="audio/mpeg")


@app.post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")
    # Optional: debug log
    print(f"from={from_number} mil={settings['MIL_NUMBER']}")

    if from_number == settings["MIL_NUMBER"]:
        if settings.get("ACTIVE_AUDIO_FILE"):
            audio_url = f"https://calls.mtup.xyz/audio/{settings['ACTIVE_AUDIO_FILE']}"
            return {"play": audio_url}
        else:
            # Fallback if no audio file is set, maybe just hang up.
            return {"hangup": ""}

    return {"connect": settings["FALLBACK_NUMBER"]}


@app.get("/settings")
def get_settings():
    """Return current settings."""
    return settings


@app.post("/settings")
def post_settings():
    """Update and save new settings."""
    new_data = request.json
    if (
        new_data
        and "MIL_NUMBER" in new_data
        and "FALLBACK_NUMBER" in new_data
        and "ACTIVE_AUDIO_FILE" in new_data
    ):
        settings["MIL_NUMBER"] = new_data["MIL_NUMBER"]
        settings["FALLBACK_NUMBER"] = new_data["FALLBACK_NUMBER"]

        # Handle active audio file selection
        selected_file = new_data["ACTIVE_AUDIO_FILE"]
        if selected_file is None:
            settings["ACTIVE_AUDIO_FILE"] = None
        else:
            # Security: ensure the file exists in our audio dir before setting
            audio_file_path = os.path.join(AUDIO_DIR, selected_file)
            if os.path.isfile(audio_file_path):
                settings["ACTIVE_AUDIO_FILE"] = selected_file
            else:
                return {"status": "error", "message": "Invalid audio file."}, 400

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

        return {"status": "success", "settings": settings}

    return {"status": "error", "message": "Invalid payload"}, 400


@app.get("/audio_files")
def list_audio_files():
    """Return a list of available audio files as a JSON array."""
    try:
        # List only files, ignore directories, filter for mp3
        files = [
            f
            for f in os.listdir(AUDIO_DIR)
            if os.path.isfile(os.path.join(AUDIO_DIR, f)) and f.lower().endswith(".mp3")
        ]
        response.content_type = "application/json"
        return json.dumps(sorted(files))
    except FileNotFoundError:
        # If the audio directory doesn't exist, create it and return empty list.
        os.makedirs(AUDIO_DIR)
        response.content_type = "application/json"
        return json.dumps([])
    except Exception as e:
        print(f"Error listing audio files: {e}")
        return {"status": "error", "message": "Could not list audio files."}, 500


@app.post("/upload_audio")
def upload_audio():
    """Handle audio file uploads."""
    upload = request.files.get("audio_file")
    if not upload:
        return {"status": "error", "message": "No file provided."}, 400

    # Basic filename sanitization to prevent directory traversal etc.
    # We'll allow alphanumeric, spaces, hyphens, and underscores.
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
        # Ensure directory exists
        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)
        upload.save(save_path)
        return {"status": "success", "filename": filename}
    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        return {"status": "error", "message": "Failed to save file."}, 500
