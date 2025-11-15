import os
import sys
import time
from pathlib import Path

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv


def test_app_integration():
    """Test the complete app integration with existing audio files"""

    print("🧪 Testing App Integration with Existing Audio Files")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    try:
        from app import AIConversation

        # Initialize conversation manager
        conversation_manager = AIConversation()

        # Test API key configuration
        print("🔑 Testing API Key Configuration:")
        print(
            f"  Soniox API Key: {'✅ Configured' if conversation_manager.soniox_api_key else '❌ Missing'}"
        )
        print(
            f"  DeepSeek API Key: {'✅ Configured' if conversation_manager.deepseek_api_key else '❌ Missing'}"
        )
        print(
            f"  ElevenLabs API Key: {'✅ Configured' if conversation_manager.elevenlabs_api_key else '❌ Missing'}"
        )

        if not conversation_manager.soniox_api_key:
            print("❌ Cannot test - Soniox API key not configured")
            return False

        # Test with a local audio file that exists
        audio_dir = Path("audio")
        if not audio_dir.exists():
            print("❌ Audio directory not found")
            return False

        # List available audio files
        audio_files = list(audio_dir.glob("*.mp3"))
        if not audio_files:
            print("❌ No audio files found in audio directory")
            return False

        print(f"🎵 Found {len(audio_files)} audio files")

        # Test with the first available audio file
        test_audio_file = audio_files[0]
        print(f"🎵 Using audio file: {test_audio_file.name}")

        # Create a simple HTTP server to serve the audio file locally
        import threading
        from http.server import HTTPServer, SimpleHTTPRequestHandler

        # Start a simple HTTP server in a separate thread
        server_address = ("localhost", 8001)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)

        def run_server():
            httpd.serve_forever()

        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

        print("🌐 Started local HTTP server on port 8001")
        time.sleep(1)  # Give server time to start

        # Test audio URL (pointing to our local server)
        test_audio_url = f"http://localhost:8001/audio/{test_audio_file.name}"
        print(f"🔗 Testing with audio URL: {test_audio_url}")

        try:
            # Test the speech_to_text method
            print("🎙️  Testing speech_to_text...")
            start_time = time.time()

            result = conversation_manager.speech_to_text(test_audio_url)

            elapsed_time = time.time() - start_time

            if result:
                print(f"✅ SUCCESS! Speech-to-text result: '{result}'")
                print(f"⏱️  Completed in {elapsed_time:.2f} seconds")

                # Test LLM response generation
                print("\n🤖 Testing LLM response generation...")
                llm_start_time = time.time()

                llm_response = conversation_manager.generate_response(result)

                llm_elapsed_time = time.time() - llm_start_time

                if llm_response:
                    print(f"✅ SUCCESS! LLM response: '{llm_response}'")
                    print(f"⏱️  Completed in {llm_elapsed_time:.2f} seconds")

                    # Test TTS (text-to-speech)
                    print("\n🔊 Testing text-to-speech...")
                    tts_start_time = time.time()

                    # Use a test call ID
                    test_call_id = "test-integration-123"
                    audio_path = conversation_manager.text_to_speech(
                        llm_response, test_call_id, 1
                    )

                    tts_elapsed_time = time.time() - tts_start_time

                    if audio_path and Path(audio_path).exists():
                        print(f"✅ SUCCESS! TTS audio saved to: {audio_path}")
                        print(f"⏱️  Completed in {tts_elapsed_time:.2f} seconds")

                        # Test complete conversation pipeline
                        print("\n🔄 Testing complete conversation pipeline...")
                        pipeline_start_time = time.time()

                        audio_path, response_text = (
                            conversation_manager.process_conversation_turn(
                                test_audio_url, test_call_id, 1
                            )
                        )

                        pipeline_elapsed_time = time.time() - pipeline_start_time

                        if audio_path and response_text:
                            print(f"✅ SUCCESS! Complete pipeline working!")
                            print(f"  Response: '{response_text}'")
                            print(f"  Audio: {audio_path}")
                            print(
                                f"⏱️  Completed in {pipeline_elapsed_time:.2f} seconds"
                            )

                            print(
                                "\n🎉 ALL TESTS PASSED! App integration is fully functional."
                            )
                            return True
                        else:
                            print("❌ Complete pipeline test failed")
                            return False
                    else:
                        print("❌ TTS test failed")
                        return False
                else:
                    print("❌ LLM response generation failed")
                    return False
            else:
                print(f"❌ Speech-to-text failed (took {elapsed_time:.2f} seconds)")
                return False

        finally:
            # Stop the HTTP server
            httpd.shutdown()
            print("🌐 Stopped local HTTP server")

    except Exception as e:
        print(f"❌ App integration test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_settings_endpoints():
    """Test that settings endpoints are working"""

    print("\n⚙️  Testing Settings Endpoints")
    print("=" * 50)

    try:
        import requests

        # Test GET /settings
        response = requests.get("http://localhost:8000/settings", timeout=10)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ GET /settings successful")
            print(f"  MIL_NUMBER: {settings.get('MIL_NUMBER', 'Not set')}")
            print(
                f"  AI_REPLIES_ENABLED: {settings.get('AI_REPLIES_ENABLED', 'Not set')}"
            )
        else:
            print(f"❌ GET /settings failed: {response.status_code}")
            return False

        # Test POST /settings (AI settings)
        ai_settings = {"AI_REPLIES_ENABLED": True, "MAX_TURNS": 3, "LANG": "sv"}

        response = requests.post(
            "http://localhost:8000/settings",
            json=ai_settings,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("✅ POST /settings (AI settings) successful")
            else:
                print(
                    f"❌ POST /settings failed: {result.get('message', 'Unknown error')}"
                )
                return False
        else:
            print(f"❌ POST /settings failed: {response.status_code}")
            return False

        return True

    except Exception as e:
        print(f"❌ Settings endpoints test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("🔍 Complete App Integration Test Suite")
    print("=" * 50)

    # Check if app is running
    try:
        import requests

        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("⚠️  App not running on localhost:8000")
            print("Please start the app first: python app.py")
            sys.exit(1)
    except:
        print("⚠️  App not running on localhost:8000")
        print("Please start the app first: python app.py")
        sys.exit(1)

    # Run tests
    settings_success = test_settings_endpoints()

    if settings_success:
        print("\n" + "=" * 50)
        print("🚀 Testing AI conversation integration...")
        app_success = test_app_integration()

        if app_success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("\n📝 System Status:")
            print("✅ Dashboard settings working")
            print("✅ Soniox STT integration working")
            print("✅ DeepSeek LLM integration working")
            print("✅ ElevenLabs TTS integration working")
            print("✅ Complete conversation pipeline working")
            print("\n🚀 Ready for production deployment!")
        else:
            print("\n💥 AI conversation integration test failed")
    else:
        print("\n💥 Settings endpoints test failed")

    print("\n🔧 Next steps:")
    print("1. Deploy to production")
    print("2. Test with actual phone calls")
    print("3. Monitor API usage and performance")
