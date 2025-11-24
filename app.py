import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from bottle import Bottle, request, response, static_file

app = Bottle()


# CORS middleware
@app.hook("after_request")
def enable_cors():
    """Add CORS headers to all responses."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token"
    )


# --- Embedded AI Conversation Module ---


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
            # Use current Soniox API - create transcription request
            soniox_url = "https://api.soniox.com/v1/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.soniox_api_key}",
                "Content-Type": "application/json",
            }

            # Create transcription request
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

            # Poll for transcription result (simple synchronous approach)
            max_attempts = 20
            for attempt in range(max_attempts):
                time.sleep(3)  # Wait 3 seconds between checks

                # Get transcription status
                status_url = f"{soniox_url}/{transcription_id}"
                status_response = requests.get(status_url, headers=headers, timeout=10)
                status_response.raise_for_status()

                status_data = status_response.json()
                status = status_data["status"]

                if status == "completed":
                    # Get the transcript
                    transcript_url = f"{soniox_url}/{transcription_id}/transcript"
                    transcript_response = requests.get(
                        transcript_url, headers=headers, timeout=10
                    )
                    transcript_response.raise_for_status()

                    transcript_data = transcript_response.json()

                    # Extract text from result
                    if "text" in transcript_data:
                        text = transcript_data["text"]
                        print(f"🎙️  STT Result: {text}")
                        return text
                    else:
                        print("❌ No transcription text in result")
                        return None

                elif status == "error":
                    print(
                        f"❌ Transcription failed: {status_data.get('error_message', 'Unknown error')}"
                    )
                    return None

                print(
                    f"⏳ Transcription status: {status} (attempt {attempt + 1}/{max_attempts})"
                )

            print(
                f"❌ Transcription timeout - took too long to complete (waited {max_attempts * 3} seconds)"
            )
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
            # Build conversation context
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful, warm, and reassuring assistant speaking to someone who may have memory challenges.
Keep responses brief (1-2 sentences), clear, and comforting. Speak in Swedish.
Focus on being present and supportive rather than solving complex problems.""",
                }
            ]

            # Add conversation history if available
            if conversation_history:
                for turn in conversation_history:
                    messages.append({"role": "user", "content": turn["user"]})
                    messages.append({"role": "assistant", "content": turn["assistant"]})

            # Add current user input
            messages.append({"role": "user", "content": user_input})

            # Call DeepSeek API
            deepseek_url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": 150,
                "temperature": 0.7,
            }

            response = requests.post(
                deepseek_url, headers=headers, json=payload, timeout=30
            )
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
            # Call ElevenLabs API
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.default_voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key,
            }

            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                },
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            # Save the audio file
            filename = f"reply-{call_id}-{turn_number}.mp3"
            filepath = self.audio_dir / filename

            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"🔊 TTS saved: {filename} ({len(response.content)} bytes)")
            return str(filepath)

        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            return None

    def process_conversation_turn(
        self,
        audio_url: str,
        call_id: str,
        turn_number: int,
        conversation_history: list = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Process a complete conversation turn: STT → LLM → TTS"""
        start_time = time.time()

        # Step 1: Speech to Text
        user_text = self.speech_to_text(audio_url)
        if not user_text:
            print("❌ STT failed, using fallback")
            return None, None

        stt_time = time.time() - start_time

        # Step 2: Generate AI Response
        ai_response = self.generate_response(user_text, conversation_history)
        if not ai_response:
            print("❌ LLM failed, using fallback")
            return None, None

        llm_time = time.time() - start_time - stt_time

        # Step 3: Text to Speech
        audio_path = self.text_to_speech(ai_response, call_id, turn_number)

        tts_time = time.time() - start_time - stt_time - llm_time
        total_time = time.time() - start_time

        print(
            f"⏱️  Timing - STT: {stt_time:.2f}s, LLM: {llm_time:.2f}s, TTS: {tts_time:.2f}s, Total: {total_time:.2f}s"
        )

        return audio_path, ai_response


# Global conversation manager instance
conversation_manager = AIConversation()

# --- Configuration & Setup ---
SETTINGS_FILE = "settings.json"
AUDIO_DIR = "audio"

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
    print(f"💾 Attempting to save settings to {SETTINGS_FILE}")
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        print(f"✅ Settings saved successfully to {SETTINGS_FILE}")
    except Exception as e:
        print(f"❌ ERROR saving settings to {SETTINGS_FILE}: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


def _get_active_audio():
    """
    Determines the correct audio file to play based on the schedule.
    Returns the filename of the audio to play, or None if no audio should be played.
    """
    active_slot = _get_active_schedule_slot()
    if active_slot:
        return active_slot["audio_file"]

    # If no schedule matches, return the default active audio file
    return settings.get("ACTIVE_AUDIO_FILE")


def _get_active_schedule_slot():
    """
    Determines the active schedule slot based on current time.
    Returns the schedule slot dict or None if no slot is active.
    """
    # Use UTC for server-side time comparison
    now = datetime.utcnow().time()

    # Check for an active scheduled item
    for slot in settings.get("SCHEDULE", []):
        try:
            start_time = datetime.strptime(slot["start_time"], "%H:%M").time()
            end_time = datetime.strptime(slot["end_time"], "%H:%M").time()

            # Handle overnight schedules (e.g., 22:00 to 02:00)
            if start_time <= end_time:
                # Normal same-day schedule
                if start_time <= now < end_time:
                    return slot
            else:
                # Overnight schedule (spans across midnight)
                if now >= start_time or now < end_time:
                    return slot
        except (ValueError, KeyError) as e:
            print(f"Skipping invalid schedule slot: {slot}. Error: {e}")
            continue

    return None


# --- Static & UI Endpoints ---
@app.get("/")
def index():
    return static_file("index.html", root="/app")


@app.route("/", method="OPTIONS")
@app.route("/<path:path>", method="OPTIONS")
def options_handler(path=None):
    """Handle OPTIONS requests for CORS preflight."""
    return {}


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

    # Check if AI voice chat is enabled for current schedule slot
    active_slot = _get_active_schedule_slot()
    ai_voice_chat_enabled = False

    if active_slot:
        # Use AI voice chat if explicitly enabled for this slot
        ai_voice_chat_enabled = active_slot.get("ai_voice_chat_enabled", False)
    else:
        # Use global AI setting if no schedule slot is active
        ai_voice_chat_enabled = settings.get("AI_REPLIES_ENABLED", True)

    if not ai_voice_chat_enabled:
        # Fallback to original behavior - play scheduled audio
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
    """Update and save general settings (MIL, Fallback, default audio, AI settings)."""
    try:
        print(f"🔧 POST /settings received request")
        new_data = request.json
        print(f"📝 Parsed JSON data: {new_data}")

        if not new_data:
            response.content_type = "application/json"
            return {"status": "error", "message": "No data provided."}, 400

        print(f"📝 Processing settings update with keys: {list(new_data.keys())}")

        # Update general settings if provided
        if "MIL_NUMBER" in new_data:
            settings["MIL_NUMBER"] = new_data["MIL_NUMBER"]
        if "FALLBACK_NUMBER" in new_data:
            settings["FALLBACK_NUMBER"] = new_data["FALLBACK_NUMBER"]

        # Update AI settings if provided
        if "MAX_TURNS" in new_data:
            settings["MAX_TURNS"] = new_data["MAX_TURNS"]
        if "LANG" in new_data:
            settings["LANG"] = new_data["LANG"]
        if "AI_REPLIES_ENABLED" in new_data:
            settings["AI_REPLIES_ENABLED"] = new_data["AI_REPLIES_ENABLED"]

        # Update active audio file if provided
        if "ACTIVE_AUDIO_FILE" in new_data:
            selected_file = new_data["ACTIVE_AUDIO_FILE"]
            print(f"🎵 Processing ACTIVE_AUDIO_FILE: {selected_file}")
            if selected_file is None:
                settings["ACTIVE_AUDIO_FILE"] = None
                print("🎵 Set ACTIVE_AUDIO_FILE to None")
            else:
                audio_file_path = os.path.join(AUDIO_DIR, selected_file)
                print(f"🎵 Checking audio file path: {audio_file_path}")
                print(f"🎵 File exists: {os.path.isfile(audio_file_path)}")
                if os.path.isfile(audio_file_path):
                    settings["ACTIVE_AUDIO_FILE"] = selected_file
                    print(f"🎵 Set ACTIVE_AUDIO_FILE to {selected_file}")
                else:
                    response.content_type = "application/json"
                    print(f"❌ Audio file not found: {selected_file}")
                    return {
                        "status": "error",
                        "message": "Invalid default audio file.",
                    }, 400

        # Save settings and return success
        print(f"💾 Saving settings to file...")
        _save_settings()
        print(f"✅ Settings saved successfully")
        print(f"📋 Final settings: {settings}")
        response.content_type = "application/json"
        return {"status": "success", "settings": settings}

    except Exception as e:
        print(f"❌ ERROR in post_settings: {str(e)}")
        import traceback

        print("🔍 Full traceback:")
        traceback.print_exc()
        response.content_type = "application/json"
        return {"status": "error", "message": f"Internal server error: {str(e)}"}, 500


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
        new_start_t = datetime.strptime(data["start_time"], "%H:%M").time()
        new_end_t = datetime.strptime(data["end_time"], "%H:%M").time()
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
        existing_start_t = datetime.strptime(
            existing_slot["start_time"], "%H:%M"
        ).time()
        existing_end_t = datetime.strptime(existing_slot["end_time"], "%H:%M").time()
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
        "ai_voice_chat_enabled": data.get("ai_voice_chat_enabled", False),
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)