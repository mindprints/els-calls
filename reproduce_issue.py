import requests
import time
import subprocess
import sys

def test_calls_endpoint():
    url = "http://localhost:8000/calls"
    payload = {
        "direction": "incoming",
        "from": "+46708944906",
        "to": "+46766866828",
        "callid": "test_call_id_123"
    }
    
    print(f"Sending POST request to {url} with payload: {payload}")
    try:
        response = requests.post(url, data=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            try:
                json_resp = response.json()
                print("JSON Response:", json_resp)
            except:
                print("Response is not JSON")
        else:
            print("Request failed")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_calls_endpoint()
