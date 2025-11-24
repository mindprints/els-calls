#!/usr/bin/env python3
"""
Test runner for els-calls test suite
Runs all available tests and provides a summary
"""

import sys
import subprocess
import os

def run_test(test_file, description):
    """Run a single test file and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 els-calls Test Suite")
    print("="*60)
    
    tests = [
        ("test_network.py", "Network Connectivity Tests"),
        ("test_ai_conversation.py", "AI Conversation System Tests"),
    ]
    
    # Check if app is running for integration tests
    try:
        import requests
        response = requests.get("http://localhost:8000", timeout=2)
        if response.status_code in [200, 401]:  # 401 is OK - means app is running
            tests.append(("test_app_integration.py", "App Integration Tests"))
            print("✅ App is running - including integration tests")
        else:
            print("⚠️  App is running but returned unexpected status - skipping integration tests")
    except:
        print("⚠️  App not running on localhost:8000 - skipping integration tests")
        print("   Start the app with: python app.py")
    
    results = []
    for test_file, description in tests:
        if os.path.exists(test_file):
            success = run_test(test_file, description)
            results.append((test_file, description, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((test_file, description, None))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_file, description, success in results:
        if success is None:
            print(f"⏭️  {description}: Skipped (file not found)")
            skipped += 1
        elif success:
            print(f"✅ {description}: Passed")
            passed += 1
        else:
            print(f"❌ {description}: Failed")
            failed += 1
    
    print("="*60)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print("="*60)
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

