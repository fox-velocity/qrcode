#!/usr/bin/env python3
"""
Quick test for invalid color handling
"""

import requests
import json

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

def test_invalid_color():
    payload = {
        "name": "Test User",
        "color": "invalid-color",
        "marker_shape": "square",
        "dot_shape": "square"
    }
    
    response = requests.post(f"{API_URL}/qr-code", json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Invalid color handled gracefully")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    test_invalid_color()