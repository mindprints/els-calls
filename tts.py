import os

from dotenv.main import load_dotenv
from elevenlabs import ElevenLabs


def text_to_speech_file(
    text, voice_id, model_id="eleven_multilingual_v2", output_filename=None
):
    """
    Convert text to speech using ElevenLabs and save to file

    Args:
        text (str): Text to convert to speech
        voice_id (str): ElevenLabs voice ID
        model_id (str): Model to use (default: eleven_multilingual_v2)
        output_filename (str): Output filename (optional, will auto-generate if None)

    Returns:
        str: Path to the saved audio file
    """

    # Load environment variables
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

    # Initialize ElevenLabs client
    client = ElevenLabs(api_key=api_key)

    # Generate audio stream
    audio_stream = client.text_to_speech.stream(
        text=text, voice_id=voice_id, model_id=model_id
    )

    # Create audio directory if it doesn't exist
    audio_dir = "audio"
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    # Generate output filename if not provided
    if output_filename is None:
        # Create a safe filename from the first few words of the text
        safe_text = "".join(
            c for c in text[:30] if c.isalnum() or c in (" ", "_", "-")
        ).strip()
        safe_text = safe_text.replace(" ", "_")
        output_filename = f"tts_{safe_text}_{voice_id[:8]}.mp3"

    output_path = os.path.join(audio_dir, output_filename)

    # Collect audio data from stream and save to file
    audio_data = b""
    for chunk in audio_stream:
        if isinstance(chunk, bytes):
            audio_data += chunk

    # Save to file
    with open(output_path, "wb") as f:
        f.write(audio_data)

    print(f"Audio saved to: {output_path}")
    return output_path


# Example usage
if __name__ == "__main__":
    # Test with your voice
    output_file = text_to_speech_file(
        text="This is a test of ElevenLabs text-to-speech",
        voice_id="5JD3K0SA9QTSxc9tVNpP",
        model_id="eleven_multilingual_v2",
        output_filename="test_voice.mp3",
    )

    print(f"Successfully created: {output_file}")
