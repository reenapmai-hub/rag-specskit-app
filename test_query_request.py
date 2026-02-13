#!/usr/bin/env python
"""Test the query endpoint"""

import requests
import json

url = "http://localhost:5001/api/query"

query_data = {"question": "What is this test document about?"}

try:
    response = requests.post(url, json=query_data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
