import os
import sys
import time
from pathlib import Path

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from dotenv import load_dotenv


def test_soniox_quick():
    """Quick test with shorter audio to verify app integration"""

    print("🧪 Quick Soniox Test with Short Audio")
    print("=" * 50)

    # Load environment variables
    load_dotenv()
    soniox_api_key = os.getenv("SONIOX_API_KEY")

    if not soniox_api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return False

    print(f"🔑 API Key: {soniox_api_key[:10]}...")

    # Use a very short test audio file (1-2 seconds)
    test_audio_url = "https://soniox.com/media/examples/hello.wav"
    print(f"🎵 Using short test audio: {test_audio_url}")

    try:
        from app import AIConversation

        # Initialize conversation manager
        conversation_manager = AIConversation()

        print("🔗 Testing app integration with short audio...")
        start_time = time.time()

        # Test the speech_to_text method
        result = conversation_manager.speech_to_text(test_audio_url)

        elapsed_time = time.time() - start_time

        if result:
            print(f"✅ SUCCESS! Transcription: '{result}'")
            print(f"⏱️  Completed in {elapsed_time:.2f} seconds")
            return True
        else:
            print(f"❌ FAILED - No result returned (took {elapsed_time:.2f} seconds)")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_direct_api_quick():
    """Test direct API with short audio"""

    print("\n🔗 Testing Direct API with Short Audio")
    print("=" * 50)

    # Load environment variables
    load_dotenv()
    soniox_api_key = os.getenv("SONIOX_API_KEY")

    if not soniox_api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return False

    # Use a very short test audio file
    test_audio_url = "https://soniox.com/media/examples/hello.wav"
    print(f"🎵 Using short test audio: {test_audio_url}")

    try:
        soniox_url = "https://api.soniox.com/v1/transcriptions"
        headers = {
            "Authorization": f"Bearer {soniox_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "audio_url": test_audio_url,
            "model": "stt-async-preview",
            "language_hints": ["en"],
        }

        print("📤 Creating transcription request...")
        create_response = requests.post(
            soniox_url, headers=headers, json=payload, timeout=30
        )

        print(f"📥 Create response status: {create_response.status_code}")

        if create_response.status_code == 201:
            transcription_data = create_response.json()
            transcription_id = transcription_data["id"]
            print(f"✅ Transcription created: {transcription_id}")

            # Quick poll (shorter timeout for short audio)
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(2)

                status_url = f"{soniox_url}/{transcription_id}"
                status_response = requests.get(status_url, headers=headers, timeout=10)

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["status"]

                    print(f"⏳ Status: {status} (attempt {attempt + 1}/{max_attempts})")

                    if status == "completed":
                        transcript_url = f"{soniox_url}/{transcription_id}/transcript"
                        transcript_response = requests.get(
                            transcript_url, headers=headers, timeout=10
                        )

                        if transcript_response.status_code == 200:
                            transcript_data = transcript_response.json()
                            if "text" in transcript_data:
                                text = transcript_data["text"]
                                print(f"🎙️  Direct API result: '{text}'")
                                return True
                        break
                    elif status == "error":
                        print(
                            f"❌ Transcription failed: {status_data.get('error_message', 'Unknown error')}"
                        )
                        return False
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False

            print("❌ Timeout waiting for transcription")
            return False
        else:
            print(f"❌ Failed to create transcription: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False

    except Exception as e:
        print(f"❌ Direct API test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔍 Quick Soniox Integration Test")
    print("=" * 50)

    # Test direct API first
    direct_success = test_direct_api_quick()

    if direct_success:
        print("\n" + "=" * 50)
        print("🚀 Testing app integration...")
        app_success = test_soniox_quick()

        if app_success:
            print("\n🎉 ALL TESTS PASSED! Soniox integration is working correctly.")
            print("\n📝 Next steps:")
            print("1. Deploy the updated app to production")
            print("2. Test with actual phone calls")
            print("3. Monitor Soniox dashboard for usage")
        else:
            print("\n💥 App integration test failed")
    else:
        print("\n💥 Direct API test failed")

    print("\n🔧 Summary:")
    print("- Soniox API is now using current endpoints and authentication")
    print("- Updated to use Bearer token authentication")
    print("- Using async transcription with polling")
    print("- Fixed response parsing to use 'text' field")
