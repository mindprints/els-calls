import os
import sys
import time
from pathlib import Path

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from dotenv import load_dotenv


def test_soniox_updated_api():
    """Test the updated Soniox API integration"""

    print("🧪 Testing Updated Soniox API Integration")
    print("=" * 50)

    # Load environment variables
    load_dotenv()
    soniox_api_key = os.getenv("SONIOX_API_KEY")

    if not soniox_api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return False

    print(f"🔑 API Key: {soniox_api_key[:10]}...")

    # Test with a sample audio URL (using a public test audio file)
    test_audio_url = "https://soniox.com/media/examples/coffee_shop.mp3"
    print(f"🎵 Using test audio URL: {test_audio_url}")

    try:
        # Use current Soniox API - create transcription request
        soniox_url = "https://api.soniox.com/v1/transcriptions"
        headers = {
            "Authorization": f"Bearer {soniox_api_key}",
            "Content-Type": "application/json",
        }

        # Create transcription request
        payload = {
            "audio_url": test_audio_url,
            "model": "stt-async-preview",
            "language_hints": ["en"],  # English for the test file
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
            print(f"📊 Initial status: {transcription_data['status']}")

            # Poll for transcription result
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(2)  # Wait 2 seconds between checks

                # Get transcription status
                status_url = f"{soniox_url}/{transcription_id}"
                status_response = requests.get(status_url, headers=headers, timeout=10)

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["status"]

                    print(f"⏳ Status check {attempt + 1}/{max_attempts}: {status}")

                    if status == "completed":
                        # Get the transcript
                        transcript_url = f"{soniox_url}/{transcription_id}/transcript"
                        transcript_response = requests.get(
                            transcript_url, headers=headers, timeout=10
                        )

                        if transcript_response.status_code == 200:
                            transcript_data = transcript_response.json()

                            # Extract text from result
                            if "text" in transcript_data:
                                text = transcript_data["text"]
                                print(f"🎙️  Transcription result: '{text}'")
                                print("✅ Updated Soniox API integration is working!")
                                return True
                            else:
                                print("❌ No transcription text in result")
                                print(f"Full response: {transcript_data}")
                                return False
                        else:
                            print(
                                f"❌ Failed to get transcript: {transcript_response.status_code}"
                            )
                            print(f"Response: {transcript_response.text}")
                            return False

                    elif status == "error":
                        error_msg = status_data.get("error_message", "Unknown error")
                        print(f"❌ Transcription failed: {error_msg}")
                        return False

                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    print(f"Response: {status_response.text}")
                    return False

            print("❌ Transcription timeout - took too long to complete")
            return False

        elif create_response.status_code == 401:
            print("❌ Authentication failed - Invalid API key")
            return False
        elif create_response.status_code == 400:
            print(f"❌ Bad request: {create_response.text}")
            return False
        else:
            print(f"❌ Unexpected status: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timeout - Soniox API took too long to respond")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_app_integration():
    """Test the app's AIConversation class with updated Soniox API"""

    print("\n🔗 Testing App Integration")
    print("=" * 50)

    try:
        from app import AIConversation

        # Initialize conversation manager
        conversation_manager = AIConversation()

        # Test API key configuration
        print(
            f"🔑 Soniox API Key: {'✅ Configured' if conversation_manager.soniox_api_key else '❌ Missing'}"
        )

        if conversation_manager.soniox_api_key:
            # Test with a simple audio URL
            test_audio_url = "https://soniox.com/media/examples/coffee_shop.mp3"
            print(f"🎵 Testing with audio URL: {test_audio_url}")

            # This will test the actual speech_to_text method
            result = conversation_manager.speech_to_text(test_audio_url)

            if result:
                print(f"✅ App integration successful! Result: '{result}'")
                return True
            else:
                print("❌ App integration failed - no result returned")
                return False
        else:
            print("❌ Cannot test app integration - API key not configured")
            return False

    except Exception as e:
        print(f"❌ App integration test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔍 Updated Soniox API Test Suite")
    print("=" * 50)

    # Test direct API integration
    api_success = test_soniox_updated_api()

    if api_success:
        print("\n" + "=" * 50)
        print("🚀 Testing app integration...")
        app_success = test_app_integration()

        if app_success:
            print(
                "\n🎉 All tests passed! The updated Soniox integration is working correctly."
            )
            print("\n📝 Next steps:")
            print("1. Deploy the updated app to production")
            print("2. Test with actual phone calls")
            print("3. Monitor Soniox dashboard for usage")
        else:
            print("\n💥 App integration test failed")
    else:
        print("\n💥 API integration test failed")

    print("\n🔧 Troubleshooting:")
    print("- Check SONIOX_API_KEY is set correctly")
    print("- Verify API key has credits and is active")
    print("- Check network connectivity to api.soniox.com")
    print("- Contact Soniox support if issues persist")
