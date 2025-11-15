import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


def test_soniox_current_api():
    """Test current Soniox API endpoints based on latest documentation"""

    print("🧪 Testing Current Soniox API Endpoints")
    print("=" * 50)

    # Load environment variables
    load_dotenv()
    soniox_api_key = os.getenv("SONIOX_API_KEY")

    if not soniox_api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return False

    print(f"🔑 API Key: {soniox_api_key[:10]}...")

    # Current Soniox API endpoints based on documentation
    endpoints = [
        # Current production endpoints
        ("https://api.soniox.com/v1/transcribe_file", "POST", "transcribe_file"),
        ("https://api.soniox.com/v1/transcribe", "POST", "transcribe"),
        (
            "https://api.soniox.com/v1/get_transcription_status",
            "GET",
            "get_transcription_status",
        ),
        (
            "https://api.soniox.com/v1/get_transcription_result",
            "GET",
            "get_transcription_result",
        ),
        # Alternative endpoints that might work
        ("https://api.soniox.com/transcribe", "POST", "transcribe_alt"),
        ("https://api.soniox.com/transcribe_file", "POST", "transcribe_file_alt"),
        # Check if base API is accessible
        ("https://api.soniox.com/", "GET", "api_root"),
        ("https://api.soniox.com/v1/", "GET", "v1_root"),
    ]

    # Test audio file
    test_audio_path = Path("audio/hello.mp3")
    if not test_audio_path.exists():
        print(f"❌ Test audio file not found: {test_audio_path}")
        return False

    print(f"🎵 Using test audio: {test_audio_path}")

    all_results = []

    for url, method, endpoint_name in endpoints:
        print(f"\n🔍 Testing {endpoint_name}: {method} {url}")

        try:
            headers = {"X-API-KEY": soniox_api_key}

            if method == "GET":
                # For GET requests, just test connectivity
                response = requests.get(url, headers=headers, timeout=10)
                result = {
                    "endpoint": endpoint_name,
                    "url": url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "success": response.status_code in [200, 201, 202],
                }

            else:  # POST requests
                # Read audio file
                with open(test_audio_path, "rb") as f:
                    audio_data = f.read()

                files = {"file": ("test.mp3", audio_data, "audio/mpeg")}
                data = {"language": "sv"}

                response = requests.post(
                    url, headers=headers, files=files, data=data, timeout=30
                )

                result = {
                    "endpoint": endpoint_name,
                    "url": url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "success": response.status_code in [200, 201, 202],
                }

                # Try to parse response if successful
                if result["success"]:
                    try:
                        response_data = response.json()
                        result["response_data"] = response_data
                        if "words" in response_data:
                            text = " ".join(
                                [word["text"] for word in response_data["words"]]
                            )
                            result["transcription"] = text
                    except:
                        result["response_text"] = response.text
                else:
                    result["response_text"] = response.text

        except requests.exceptions.ConnectionError as e:
            result = {
                "endpoint": endpoint_name,
                "url": url,
                "status_code": "CONNECTION_ERROR",
                "error": str(e),
                "success": False,
            }
        except requests.exceptions.Timeout as e:
            result = {
                "endpoint": endpoint_name,
                "url": url,
                "status_code": "TIMEOUT",
                "error": str(e),
                "success": False,
            }
        except Exception as e:
            result = {
                "endpoint": endpoint_name,
                "url": url,
                "status_code": "ERROR",
                "error": str(e),
                "success": False,
            }

        # Display result
        if result["success"]:
            print(f"   ✅ SUCCESS - Status: {result['status_code']}")
            if "transcription" in result:
                print(f"   🎙️  Transcription: '{result['transcription']}'")
        else:
            print(f"   ❌ FAILED - Status: {result.get('status_code', 'UNKNOWN')}")
            if "error" in result:
                print(f"   Error: {result['error']}")
            elif "response_text" in result:
                print(f"   Response: {result['response_text'][:100]}...")

        all_results.append(result)

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    successful_endpoints = [r for r in all_results if r["success"]]
    failed_endpoints = [r for r in all_results if not r["success"]]

    print(f"✅ Successful: {len(successful_endpoints)} endpoints")
    print(f"❌ Failed: {len(failed_endpoints)} endpoints")

    if successful_endpoints:
        print("\n🎉 Working endpoints:")
        for result in successful_endpoints:
            print(f"  • {result['endpoint']} ({result['url']})")

    if failed_endpoints:
        print("\n💥 Failed endpoints:")
        for result in failed_endpoints:
            status = result.get("status_code", "UNKNOWN")
            error = result.get("error", result.get("response_text", "No details"))
            print(f"  • {result['endpoint']}: {status} - {error}")

    # Recommendations
    print("\n🔧 RECOMMENDATIONS")
    print("=" * 50)

    if successful_endpoints:
        print("✅ Update the app to use working endpoints:")
        for result in successful_endpoints:
            print(f"   - {result['url']}")
    else:
        print("❌ No working endpoints found. Possible issues:")
        print("   1. Soniox API might be down or undergoing maintenance")
        print("   2. API key might be invalid or expired")
        print("   3. Network/firewall restrictions")
        print("   4. API endpoints have changed")
        print("\n📚 Check current documentation: https://docs.soniox.com/")
        print("📧 Contact support: support@soniox.com")
        print("🔗 Status page: https://status.soniox.com/")

    return len(successful_endpoints) > 0


def check_soniox_documentation_updates():
    """Check for recent changes to Soniox API"""
    print("\n📚 Checking for Soniox API Updates")
    print("=" * 50)

    print("Recent changes to Soniox API (based on common patterns):")
    print("• Endpoints may have moved from /v1/ to root /")
    print("• Parameter names may have changed")
    print("• Authentication headers may have been updated")
    print("• New endpoints for streaming/real-time transcription")

    print("\n🔗 Current documentation: https://docs.soniox.com/")
    print("📝 API reference: https://docs.soniox.com/api-reference")
    print("🚀 Quick start: https://docs.soniox.com/quick-start")


if __name__ == "__main__":
    print("🔍 Soniox API Current Endpoint Test")
    print("=" * 50)

    success = test_soniox_current_api()
    check_soniox_documentation_updates()

    if success:
        print("\n🎉 Update successful! Working endpoints found.")
    else:
        print("\n💥 No working endpoints found. Manual investigation required.")
