import os
import sys
from pathlib import Path

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json

import requests
from dotenv import load_dotenv


def test_soniox_api():
    """Test Soniox API connection and functionality"""

    # Load environment variables
    load_dotenv()

    # Get API key from environment
    soniox_api_key = os.getenv("SONIOX_API_KEY")

    if not soniox_api_key:
        print("❌ SONIOX_API_KEY not found in environment variables")
        print("Please set SONIOX_API_KEY in your .env file or environment")
        return False

    print(f"🔑 Soniox API Key: {soniox_api_key[:10]}... (first 10 chars)")

    # Test with a sample audio file
    test_audio_path = Path("audio/hello.mp3")

    if not test_audio_path.exists():
        print(f"❌ Test audio file not found: {test_audio_path}")
        print("Please ensure hello.mp3 exists in the audio directory")
        return False

    print(f"🎵 Using test audio file: {test_audio_path}")

    try:
        # Read the audio file
        with open(test_audio_path, "rb") as audio_file:
            audio_data = audio_file.read()

        # Prepare request to Soniox
        soniox_url = "https://api.soniox.com/v1/transcribe_async"
        headers = {"X-API-KEY": soniox_api_key}

        files = {"audio_file": ("test_audio.mp3", audio_data, "audio/mpeg")}
        data = {"language_code": "sv"}  # Swedish

        print("📤 Sending request to Soniox API...")

        # Make the API call
        response = requests.post(
            soniox_url, headers=headers, files=files, data=data, timeout=30
        )

        print(f"📥 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Soniox API connection successful!")
            print(f"📝 Response keys: {list(result.keys())}")

            if "words" in result:
                text = " ".join([word["text"] for word in result["words"]])
                print(f"🎙️  Transcription result: '{text}'")
            else:
                print("❓ No transcription words in response")
                print(f"Full response: {json.dumps(result, indent=2)}")

            return True

        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key")
            return False
        elif response.status_code == 403:
            print("❌ Forbidden - Check API key permissions")
            return False
        elif response.status_code == 429:
            print("❌ Rate limit exceeded")
            return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timeout - Soniox API took too long to respond")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Could not reach Soniox API")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_environment_variables():
    """Test if all required environment variables are set"""
    print("\n🔍 Checking environment variables...")

    load_dotenv()

    required_vars = ["SONIOX_API_KEY", "DEEPSEEK_API_KEY", "ELEVENLABS_API_KEY"]

    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}... (first 10 chars)")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False

    return all_set


if __name__ == "__main__":
    print("🧪 Soniox API Test Script")
    print("=" * 50)

    # Test environment variables first
    env_ok = test_environment_variables()

    if env_ok:
        print("\n" + "=" * 50)
        print("🚀 Testing Soniox API connection...")
        api_ok = test_soniox_api()

        if api_ok:
            print("\n🎉 All tests passed! Soniox integration should work.")
        else:
            print("\n💥 Soniox API test failed. Check the errors above.")
    else:
        print("\n💥 Missing environment variables. Please set them in .env file.")

    print("\n📝 Next steps:")
    print("1. Check Soniox dashboard for API usage")
    print("2. Verify API key is active and has credits")
    print("3. Test with actual phone calls")
