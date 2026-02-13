#!/usr/bin/env python
"""Test the upload endpoint"""

import requests

url = "http://localhost:5001/api/upload"
test_file = "test_upload.txt"

with open(test_file, "rb") as f:
    files = {"file": f}
    try:
        response = requests.post(url, files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
