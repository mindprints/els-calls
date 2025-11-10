import json

from bottle import Bottle, request, static_file

app = Bottle()

# Global settings dictionary, loaded from file
SETTINGS_FILE = "/app/settings.json"
with open(SETTINGS_FILE, "r") as f:
    settings = json.load(f)


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
        return {"play": "https://calls.mtup.xyz/audio/Aha-remix.mp3"}

    return {"connect": settings["FALLBACK_NUMBER"]}


@app.get("/settings")
def get_settings():
    """Return current settings."""
    return settings


@app.post("/settings")
def post_settings():
    """Update and save new settings."""
    new_data = request.json
    if new_data and "MIL_NUMBER" in new_data and "FALLBACK_NUMBER" in new_data:
        settings["MIL_NUMBER"] = new_data["MIL_NUMBER"]
        settings["FALLBACK_NUMBER"] = new_data["FALLBACK_NUMBER"]

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

        return {"status": "success", "settings": settings}

    return {"status": "error", "message": "Missing required fields"}, 400
