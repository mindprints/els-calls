import os
import socket
import ssl
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


def test_ssl_certificate(hostname):
    """Test SSL certificate for a hostname"""
    print(f"🔐 Testing SSL certificate for: {hostname}")
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                print(f"✅ SSL certificate valid for: {hostname}")
                print(f"   Subject: {cert.get('subject', 'N/A')}")
                print(f"   Issuer: {cert.get('issuer', 'N/A')}")
                print(f"   Expires: {cert.get('notAfter', 'N/A')}")
                return True
    except ssl.SSLCertVerificationError as e:
        print(f"❌ SSL certificate verification failed: {e}")
        return False
    except Exception as e:
        print(f"❌ SSL connection failed: {e}")
        return False


def test_soniox_endpoints():
    """Test different Soniox API endpoints"""
    print("\n🎯 Testing Soniox API Endpoints")
    print("=" * 50)

    endpoints = [
        ("v1/transcribe_async", "POST"),
        ("v1/transcribe", "POST"),
        ("v1/transcribe_file", "POST"),
        ("v1/get_transcription", "GET"),
        ("", "GET"),  # Root endpoint
    ]

    soniox_api_key = os.getenv("SONIOX_API_KEY")
    base_url = "https://api.soniox.com"

    for endpoint, method in endpoints:
        url = f"{base_url}/{endpoint}" if endpoint else base_url
        print(f"\n🔍 Testing {method} {url}")

        try:
            if method == "GET":
                response = requests.get(url, timeout=10, verify=True)
            else:
                # For POST requests, send minimal data
                headers = {"X-API-KEY": soniox_api_key} if soniox_api_key else {}
                response = requests.post(
                    url,
                    headers=headers,
                    json={} if method == "POST" else None,
                    timeout=10,
                    verify=True,
                )

            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")

            if response.status_code == 200:
                print("   ✅ Endpoint accessible")
            elif response.status_code == 404:
                print("   ❌ Endpoint not found")
            elif response.status_code == 401:
                print("   🔐 Authentication required")
            elif response.status_code == 405:
                print("   ⚠️  Method not allowed")
            else:
                print(f"   ❓ Unexpected status: {response.status_code}")

        except requests.exceptions.SSLError as e:
            print(f"   ❌ SSL Error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_with_ssl_verify_disabled():
    """Test Soniox API with SSL verification disabled"""
    print("\n🚫 Testing with SSL Verification Disabled")
    print("=" * 50)

    soniox_api_key = os.getenv("SONIOX_API_KEY")
    if not soniox_api_key:
        print("❌ SONIOX_API_KEY not set")
        return False

    soniox_url = "https://api.soniox.com/v1/transcribe_async"

    # Test with a small audio file
    test_audio_path = Path("audio/hello.mp3")
    if not test_audio_path.exists():
        print("❌ Test audio file not found")
        return False

    try:
        with open(test_audio_path, "rb") as audio_file:
            audio_data = audio_file.read()

        headers = {"X-API-KEY": soniox_api_key}
        files = {"audio_file": ("test.mp3", audio_data, "audio/mpeg")}
        data = {"language_code": "sv"}

        print("📤 Sending request with SSL verify=False...")
        response = requests.post(
            soniox_url,
            headers=headers,
            files=files,
            data=data,
            timeout=30,
            verify=False,  # Disable SSL verification
        )

        print(f"📥 Response: Status {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful with SSL verify=False!")
            if "words" in result:
                text = " ".join([word["text"] for word in result["words"]])
                print(f"🎙️  Transcription: '{text}'")
            return True
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_soniox_documentation():
    """Check Soniox API documentation for endpoint changes"""
    print("\n📚 Checking Soniox API Documentation")
    print("=" * 50)

    # Common Soniox API endpoints from documentation
    endpoints_info = {
        "v1/transcribe_async": "Asynchronous transcription (most common)",
        "v1/transcribe": "Synchronous transcription",
        "v1/transcribe_file": "File-based transcription",
        "v1/get_transcription": "Get async transcription result",
    }

    print("Known Soniox API endpoints:")
    for endpoint, description in endpoints_info.items():
        print(f"  • {endpoint}: {description}")

    print("\n🔗 Documentation: https://docs.soniox.com/")
    print("📧 Support: support@soniox.com")


def main():
    """Main test function"""
    print("🔍 Soniox SSL and API Endpoint Diagnostics")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Test SSL certificate first
    soniox_host = "api.soniox.com"
    ssl_ok = test_ssl_certificate(soniox_host)

    if not ssl_ok:
        print("\n⚠️  SSL certificate issues detected")
        print("Testing with alternative approaches...")

    # Test various endpoints
    test_soniox_endpoints()

    # Test with SSL verification disabled
    ssl_disabled_ok = test_with_ssl_verify_disabled()

    # Check documentation
    check_soniox_documentation()

    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)

    if ssl_disabled_ok:
        print("✅ API works with SSL verification disabled")
        print("\n🔧 Solution: The issue is likely SSL certificate verification")
        print("   - Contact hosting provider about SSL/TLS configuration")
        print("   - Check if intermediate certificates are installed")
        print("   - Verify system time is correct")
    else:
        print("❌ API connectivity issues persist")
        print("\n🔧 Next steps:")
        print("1. Check Soniox API status: https://status.soniox.com/")
        print("2. Verify API key is active and has credits")
        print("3. Contact Soniox support: support@soniox.com")
        print("4. Check firewall and network configuration")
        print("5. Test from a different network/location")


if __name__ == "__main__":
    main()
