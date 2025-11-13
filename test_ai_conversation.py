"""
Test script for AI conversation system

This script tests the AI conversation functionality including:
- STT (Soniox)
- LLM (DeepSeek)
- TTS (ElevenLabs)
- Conversation flow
- Custom recorded audio files
"""

import json
import os
import sys
from pathlib import Path

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from app import AIConversation

load_dotenv()


def test_ai_conversation():
    """Test the complete AI conversation pipeline"""

    print("🧪 Testing AI Conversation System")
    print("=" * 50)

    # Initialize conversation manager
    conversation_manager = AIConversation()

    # Test API key configuration
    print("\n🔑 Testing API Key Configuration:")
    print(
        f"  Soniox API Key: {'✅ Configured' if conversation_manager.soniox_api_key else '❌ Missing'}"
    )
    print(
        f"  DeepSeek API Key: {'✅ Configured' if conversation_manager.deepseek_api_key else '❌ Missing'}"
    )
    print(
        f"  ElevenLabs API Key: {'✅ Configured' if conversation_manager.elevenlabs_api_key else '❌ Missing'}"
    )

    # Test settings loading
    print(f"\n⚙️  Settings:")
    print(f"  Max Turns: {conversation_manager.max_turns}")
    print(f"  Language: {conversation_manager.default_language}")
    print(f"  Voice ID: {conversation_manager.default_voice_id}")

    # Test TTS generation (most reliable test)
    print("\n🔊 Testing TTS Generation:")
    try:
        test_text = "Hej! Det här är ett testmeddelande för att kontrollera att allt fungerar som det ska."
        call_id = "test123"

        audio_path = conversation_manager.text_to_speech(test_text, call_id, 1)
        if audio_path and Path(audio_path).exists():
            file_size = Path(audio_path).stat().st_size
            print(f"  ✅ TTS Success: {Path(audio_path).name} ({file_size} bytes)")

            # Clean up test file
            Path(audio_path).unlink()
            print(f"  ✅ Test file cleaned up")
        else:
            print(f"  ❌ TTS Failed")

    except Exception as e:
        print(f"  ❌ TTS Error: {e}")

    # Test LLM generation
    print("\n🧠 Testing LLM Generation:")
    try:
        test_input = "Hej, hur mår du idag?"
        response = conversation_manager.generate_response(test_input)

        if response:
            print(f"  ✅ LLM Success: {response}")
        else:
            print(f"  ❌ LLM Failed")

    except Exception as e:
        print(f"  ❌ LLM Error: {e}")

    # Test conversation flow simulation
    print("\n🔄 Testing Conversation Flow:")
    try:
        # Simulate a conversation turn
        test_audio_url = "https://example.com/test.wav"  # Mock URL for testing
        call_id = "flowtest456"

        print(f"  Simulating conversation turn for call {call_id}")
        audio_path, response_text = conversation_manager.process_conversation_turn(
            test_audio_url, call_id, 1
        )

        if audio_path and response_text:
            print(f"  ✅ Conversation Success:")
            print(f"     Response: {response_text}")
            print(f"     Audio: {Path(audio_path).name}")

            # Clean up test file
            if Path(audio_path).exists():
                Path(audio_path).unlink()
                print(f"     Test file cleaned up")
        else:
            print(f"  ❌ Conversation Failed")

    except Exception as e:
        print(f"  ❌ Conversation Error: {e}")

    # Test settings integration
    print("\n📋 Testing Settings Integration:")
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)

        print(f"  MAX_TURNS: {settings.get('MAX_TURNS', 'Not set')}")
        print(f"  LANG: {settings.get('LANG', 'Not set')}")
        print(f"  AI_REPLIES_ENABLED: {settings.get('AI_REPLIES_ENABLED', 'Not set')}")
        print(f"  ✅ Settings loaded successfully")

    except Exception as e:
        print(f"  ❌ Settings Error: {e}")

    print("\n" + "=" * 50)
    print("🎉 AI Conversation System Test Complete")
    print("\n📝 Next Steps:")
    print("  1. Add API keys to .env file:")
    print("     SONIOX_API_KEY=your_soniox_key")
    print("     DEEPSEEK_API_KEY=your_deepseek_key")
    print("     ELEVENLABS_API_KEY=your_elevenlabs_key")
    print("  2. Verify custom audio files are in place:")
    print("     hello.mp3, waiting.mp3, goodbye.mp3, fallback.mp3")
    print("  3. Deploy and test with actual calls")


def test_conversation_audio_files():
    """Check if required conversation audio files exist"""

    print("\n🎵 Checking Conversation Audio Files:")

    required_files = ["hello.mp3", "waiting.mp3", "goodbye.mp3", "fallback.mp3"]
    audio_dir = Path("audio")

    for filename in required_files:
        filepath = audio_dir / filename
        if filepath.exists():
            file_size = filepath.stat().st_size
            print(f"  ✅ {filename} ({file_size} bytes)")
        else:
            print(f"  ❌ {filename} - Missing")

    if all((audio_dir / f).exists() for f in required_files):
        print("  ✅ All custom conversation audio files are ready!")
    else:
        print(
            "  ⚠️  Some audio files are missing. Please record the required MP3 files."
        )


if __name__ == "__main__":
    test_ai_conversation()
    test_conversation_audio_files()
