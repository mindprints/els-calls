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

class AIConversation:
    """Handles the AI conversation pipeline"""

    def __init__(self, audio_dir: str = "audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)

        # API Keys from environment
        self.soniox_api_key = os.getenv("SONIOX_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

        # Default settings
        self.default_voice_id = "5JD3K0SA9QTSxc9tVNpP"
        self.default_language = "sv"
        self.max_turns = 3

        # Load settings from file
        self._load_settings()

    def _load_settings(self):
        """Load settings from settings.json"""
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.max_turns = settings.get("MAX_TURNS", 3)
                self.default_language = settings.get("LANG", "sv")
        except FileNotFoundError:
            pass

    def speech_to_text(self, audio_url: str) -> Optional[str]:
        """Convert speech to text using Soniox API"""
        if not self.soniox_api_key:
            print("❌ Soniox API key not configured")
            return None

        try:
            soniox_url = "https://api.soniox.com/v1/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.soniox_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "audio_url": audio_url,
                "model": "stt-async-preview",
                "language_hints": [self.default_language],
            }

            create_response = requests.post(
                soniox_url, headers=headers, json=payload, timeout=30
            )
            create_response.raise_for_status()

            transcription_data = create_response.json()
            transcription_id = transcription_data["id"]
            print(f"📝 Created transcription: {transcription_id}")

            max_attempts = 20
            for attempt in range(max_attempts):
                time.sleep(3)
                status_url = f"{soniox_url}/{transcription_id}"
                status_response = requests.get(status_url, headers=headers, timeout=10)
                status_response.raise_for_status()

                status_data = status_response.json()
                status = status_data["status"]

                if status == "completed":
                    transcript_url = f"{soniox_url}/{transcription_id}/transcript"
                    transcript_response = requests.get(
                        transcript_url, headers=headers, timeout=10
                    )
                    transcript_response.raise_for_status()
                    transcript_data = transcript_response.json()

                    if "text" in transcript_data:
                        text = transcript_data["text"]
                        print(f"🎙️  STT Result: {text}")
                        return text
                    else:
                        print("❌ No transcription text in result")
                        return None
                elif status == "error":
                    print(f"❌ Transcription failed: {status_data.get('error_message', 'Unknown error')}")
                    return None
                print(f"⏳ Transcription status: {status} (attempt {attempt + 1}/{max_attempts})")

            print(f"❌ Transcription timeout")
            return None
        except Exception as e:
            print(f"❌ STT failed: {e}")
            return None

    def generate_response(
        self, user_input: str, conversation_history: list = None
    ) -> Optional[str]:
        """Generate AI response using DeepSeek API"""
        if not self.deepseek_api_key:
            print("❌ DeepSeek API key not configured")
            return None
        try:
            messages = [{"role": "system","content": "You are a helpful, warm, and reassuring assistant..."},]
            if conversation_history:
                for turn in conversation_history:
                    messages.append({"role": "user", "content": turn["user"]})
                    messages.append({"role": "assistant", "content": turn["assistant"]})
            messages.append({"role": "user", "content": user_input})

            deepseek_url = "https://api.deepseek.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.deepseek_api_key}","Content-Type": "application/json",}
            payload = {"model": "deepseek-chat","messages": messages,"max_tokens": 150,"temperature": 0.7,}
            response = requests.post(deepseek_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            print(f"🧠 LLM Response: {ai_response}")
            return ai_response
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            return None

    def text_to_speech(
        self, text: str, call_id: str, turn_number: int
    ) -> Optional[str]:
        """Convert text to speech using ElevenLabs"""
        if not self.elevenlabs_api_key:
            print("❌ ElevenLabs API key not configured")
            return None
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.default_voice_id}"
            headers = {"Accept": "audio/mpeg","Content-Type": "application/json","xi-api-key": self.elevenlabs_api_key,}
            data = {"text": text,"model_id": "eleven_multilingual_v2","voice_settings": {"stability": 0.5,"similarity_boost": 0.8,},}
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            filename = f"reply-{call_id}-{turn_number}.mp3"
            filepath = self.audio_dir / filename
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"🔊 TTS saved: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            return None

    def process_conversation_turn(
        self, audio_url: str, call_id: str, turn_number: int, conversation_history: list = None
    ) -> Tuple[Optional[str], Optional[str]]:
        user_text = self.speech_to_text(audio_url)
        if not user_text: return None, None
        ai_response = self.generate_response(user_text, conversation_history)
        if not ai_response: return None, None
        audio_path = self.text_to_speech(ai_response, call_id, turn_number)
        return audio_path, ai_response

conversation_manager = AIConversation()

# --- Configuration & Setup ---
SETTINGS_FILE = "settings.json"
AUDIO_DIR = "audio"
try:
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {"MIL_NUMBER": "","FALLBACK_NUMBER": "","ACTIVE_AUDIO_FILE": None,"SCHEDULE": [],"MAX_TURNS": 3,"LANG": "sv","NAMED_NUMBERS": [],}
settings.setdefault("SCHEDULE", [])
settings.setdefault("NAMED_NUMBERS", [])

def _save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def _get_active_schedule_slot():
    now_utc = datetime.utcnow()
    current_time = now_utc.time()
    current_day = now_utc.weekday()
    for slot in settings.get("SCHEDULE", []):
        try:
            if current_day not in slot.get("days", []): continue
            start_time = datetime.strptime(slot["start_time"], "%H:%M").time()
            end_time = datetime.strptime(slot["end_time"], "%H:%M").time()
            if (start_time <= current_time < end_time) if start_time <= end_time else (current_time >= start_time or current_time < end_time):
                return slot
        except (ValueError, KeyError) as e:
            print(f"Skipping invalid schedule slot: {slot}. Error: {e}")
    return None

# --- Static & UI Endpoints ---
@app.get("/")
@auth_required
def index():
    return static_file("index.html", root="/app")

@app.route("/", method="OPTIONS")
@app.route("/<path:path>", method="OPTIONS")
def options_handler(path=None): return {}

@app.get("/audio/<filename>")
@auth_required
def serve_audio(filename: str):
    return static_file(filename, root=AUDIO_DIR, mimetype="audio/mpeg")

# --- Core API ---
@app.post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")
    if from_number != settings.get("MIL_NUMBER"):
        return {"connect": settings.get("FALLBACK_NUMBER", "")}

    active_slot = _get_active_schedule_slot()
    action = active_slot.get('audio_file', 'AI_VOICE_CHAT') if active_slot else settings.get("ACTIVE_AUDIO_FILE", "AI_VOICE_CHAT")

    if action != 'AI_VOICE_CHAT':
        if os.path.isfile(os.path.join(AUDIO_DIR, action)):
            return {"play": f"https://calls.mtup.xyz/audio/{action}"}
        return {"hangup": ""}

    # AI Conversation Flow
    call_id = request.forms.get("callid")
    mode = request.query.get("mode")
    base_url = "https://calls.mtup.xyz"
    max_turns = settings.get("MAX_TURNS", 3)

    if not mode:
        return {"play": f"{base_url}/audio/hello.mp3", "skippable": False, "next": f"{base_url}/calls?mode=record1&callid={call_id}"}
    elif mode.startswith("record"):
        turn = int(mode.replace("record", ""))
        return {"record": f"{base_url}/recordings", "silencedetection": "yes", "timelimit": 12, "next": f"{base_url}/calls?mode=reply{turn}&callid={call_id}"}
    elif mode.startswith("reply"):
        turn = int(mode.replace("reply", ""))
        reply_file = f"reply-{call_id}-{turn}.mp3"
        if os.path.exists(os.path.join(AUDIO_DIR, reply_file)):
            response_data = {"play": f"{base_url}/audio/{reply_file}"}
            response_data["next"] = f"{base_url}/calls?mode=record{turn + 1}&callid={call_id}" if turn < max_turns else f"{base_url}/calls?mode=closing&callid={call_id}"
            return response_data
        else:
            return {"play": f"{base_url}/audio/waiting.mp3", "next": f"{base_url}/calls?mode=reply{turn}&callid={call_id}"}
    elif mode == "closing":
        return {"play": f"{base_url}/audio/goodbye.mp3"}
    return {"hangup": ""}

# --- Settings & Configuration API ---
@app.get("/settings")
@auth_required
def get_settings(): return settings

@app.post("/settings")
@auth_required
def post_settings():
    new_data = request.json
    for key in ["MIL_NUMBER", "FALLBACK_NUMBER", "MAX_TURNS", "LANG", "ACTIVE_AUDIO_FILE"]:
        if key in new_data: settings[key] = new_data[key]
    _save_settings()
    return {"status": "success", "settings": settings}

# --- Schedule API ---
@app.post("/schedule")
@auth_required
def add_schedule_entry():
    data = request.json
    # Basic validation
    if not all(k in data for k in ["days", "audio_file", "start_time", "end_time"]):
        return {"status": "error", "message": "Invalid payload."}, 400
    settings["SCHEDULE"].append(data)
    _save_settings()
    return {"status": "success", "schedule": settings["SCHEDULE"]}

@app.delete("/schedule/<index:int>")
@auth_required
def delete_schedule_entry(index):
    if 0 <= index < len(settings["SCHEDULE"]):
        settings["SCHEDULE"].pop(index)
        _save_settings()
        return {"status": "success", "schedule": settings["SCHEDULE"]}
    return {"status": "error", "message": "Index out of bounds."}, 404

# --- Named Numbers API ---
@app.post("/named_numbers")
@auth_required
def add_named_number():
    data = request.json
    if "name" in data and "number" in data:
        settings["NAMED_NUMBERS"].append({"name": data["name"], "number": data["number"]})
        _save_settings()
        return {"status": "success", "named_numbers": settings["NAMED_NUMBERS"]}
    return {"status": "error", "message": "Invalid payload."}, 400

@app.delete("/named_numbers/<index:int>")
@auth_required
def delete_named_number(index):
    if 0 <= index < len(settings["NAMED_NUMBERS"]):
        settings["NAMED_NUMBERS"].pop(index)
        _save_settings()
        return {"status": "success", "named_numbers": settings["NAMED_NUMBERS"]}
    return {"status": "error", "message": "Index out of bounds."}, 404

# --- Audio File Management API ---
@app.get("/audio_files")
@auth_required
def list_audio_files():
    try:
        files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
        return json.dumps(sorted(files))
    except Exception:
        return json.dumps({"status": "error", "message": "Could not list audio files."}), 500

@app.post("/upload_audio")
@auth_required
def upload_audio():
    upload = request.files.get("audio_file")
    if upload and upload.filename.lower().endswith(".mp3"):
        save_path = os.path.join(AUDIO_DIR, os.path.basename(upload.filename))
        upload.save(save_path)
        return {"status": "success", "filename": upload.filename}
    return {"status": "error", "message": "Invalid file."}, 400

@app.delete("/audio/<filename>")
@auth_required
def delete_audio_file(filename: str):
    if ".." in filename or "/" in filename:
        return {"status": "error", "message": "Invalid filename."}, 400
    try:
        file_path = os.path.join(AUDIO_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            return {"status": "success", "message": f"File '{filename}' deleted."}
        else:
            return {"status": "error", "message": "File not found."}, 404
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
    app.run(host="0.0.0.0", port=8000, debug=True)
