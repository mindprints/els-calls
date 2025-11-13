import os

from dotenv.main import load_dotenv
from elevenlabs import ElevenLabs

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

client = ElevenLabs(api_key=api_key, base_url="https://api.elevenlabs.io/")

# Generate audio from text
audio_generator = client.text_to_speech.convert(
    voice_id="5JD3K0SA9QTSxc9tVNpP",
    output_format="mp3_44100_128",
    enable_logging=True,
    optimize_streaming_latency=0,
    text="Om du bara visste vad hon tyckte om dig, du skulle gråta",
    model_id="eleven_multilingual_v2",
    language_code="sv",
    voice_settings={},
)

# Collect all audio chunks from generator
audio_data = b""
for chunk in audio_generator:
    if isinstance(chunk, bytes):
        audio_data += chunk

# Save audio to file
audio_dir = "audio"
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)

output_file = os.path.join(audio_dir, "elevenlabs_test.mp3")
with open(output_file, "wb") as f:
    f.write(audio_data)

print(f"Audio saved to: {output_file}")
