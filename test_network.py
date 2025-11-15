import json
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests


def test_dns_resolution(hostname):
    """Test DNS resolution for a hostname"""
    print(f"🔍 Testing DNS resolution for: {hostname}")
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ DNS resolution successful: {hostname} -> {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed for {hostname}: {e}")
        return False


def test_http_connection(url, timeout=10):
    """Test HTTP connection to a URL"""
    print(f"🌐 Testing HTTP connection to: {url}")
    try:
        response = requests.get(url, timeout=timeout, verify=False)
        print(f"✅ HTTP connection successful: Status {response.status_code}")
        return True
    except requests.exceptions.Timeout:
        print(f"❌ HTTP connection timeout to {url}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTP connection failed to {url}: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTP connection error to {url}: {e}")
        return False


def test_soniox_api_connectivity():
    """Test connectivity to Soniox API endpoints"""
    print("\n🎙️ Testing Soniox API Connectivity")
    print("=" * 50)

    # Test DNS resolution first
    soniox_host = "api.soniox.com"
    dns_ok = test_dns_resolution(soniox_host)

    if not dns_ok:
        print("❌ Cannot proceed - DNS resolution failed")
        return False

    # Test basic HTTP connectivity
    soniox_url = f"https://{soniox_host}/v1/transcribe_async"
    http_ok = test_http_connection(soniox_url)

    if not http_ok:
        print("❌ Cannot proceed - HTTP connection failed")
        return False

    # Test with actual API call if we have credentials
    soniox_api_key = os.getenv("SONIOX_API_KEY")
    if soniox_api_key:
        print(f"\n🔑 Testing Soniox API with credentials...")
        print(f"API Key: {soniox_api_key[:10]}...")

        # Test with a small audio file
        test_audio_path = Path("audio/hello.mp3")
        if test_audio_path.exists():
            try:
                with open(test_audio_path, "rb") as audio_file:
                    audio_data = audio_file.read()

                headers = {"X-API-KEY": soniox_api_key}
                files = {"audio_file": ("test.mp3", audio_data, "audio/mpeg")}
                data = {"language_code": "sv"}

                print("📤 Sending API request to Soniox...")
                response = requests.post(
                    soniox_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30,
                    verify=False,
                )

                print(f"📥 API Response: Status {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print("✅ Soniox API call successful!")
                    if "words" in result:
                        text = " ".join([word["text"] for word in result["words"]])
                        print(f"🎙️ Transcription: '{text}'")
                    return True
                elif response.status_code == 401:
                    print("❌ Authentication failed - Invalid API key")
                    return False
                else:
                    print(f"❌ API error: {response.status_code} - {response.text}")
                    return False

            except Exception as e:
                print(f"❌ API call failed: {e}")
                return False
        else:
            print("⚠️  Test audio file not found, skipping API call test")
            return True
    else:
        print("⚠️  SONIOX_API_KEY not set, skipping API call test")
        return True


def test_other_apis():
    """Test connectivity to other required APIs"""
    print("\n🔗 Testing Other API Connectivity")
    print("=" * 50)

    apis_to_test = [
        ("DeepSeek API", "https://api.deepseek.com"),
        ("ElevenLabs API", "https://api.elevenlabs.io"),
        ("46elks API", "https://api.46elks.com"),
    ]

    all_ok = True
    for api_name, api_url in apis_to_test:
        hostname = urlparse(api_url).hostname
        if hostname:
            dns_ok = test_dns_resolution(hostname)
            http_ok = test_http_connection(api_url)
            if not (dns_ok and http_ok):
                all_ok = False

    return all_ok


def test_local_connectivity():
    """Test local network connectivity"""
    print("\n🏠 Testing Local Network Connectivity")
    print("=" * 50)

    # Test localhost
    local_ok = test_http_connection("http://localhost:8000", timeout=5)

    # Test external connectivity
    external_ok = test_http_connection("https://www.google.com", timeout=10)

    return local_ok, external_ok


def main():
    """Main test function"""
    print("🌐 Network Connectivity Test Suite")
    print("=" * 50)

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Test local and external connectivity
    local_ok, external_ok = test_local_connectivity()

    if not external_ok:
        print("\n💥 External connectivity failed - check network/firewall")
        return

    # Test Soniox API connectivity
    soniox_ok = test_soniox_api_connectivity()

    # Test other APIs
    other_apis_ok = test_other_apis()

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    if soniox_ok and other_apis_ok:
        print("✅ All connectivity tests passed!")
        print("\n🎉 Network connectivity appears to be working correctly.")
        print("If Soniox still shows 0 usage, check:")
        print("1. API key validity and credits")
        print("2. Call flow is triggering AI conversation")
        print("3. Audio files are being recorded and sent to Soniox")
    else:
        print("❌ Some connectivity tests failed")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check firewall settings")
        print("2. Verify DNS configuration")
        print("3. Check network proxy settings")
        print("4. Contact hosting provider about outbound connectivity")


if __name__ == "__main__":
    main()
