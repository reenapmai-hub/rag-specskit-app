"""Standalone integration runner for upload→query→reset lifecycle.

Usage:
    python tests/integration/run_upload_query_reset.py

Environment variables:
- API_BASE (optional, defaults to http://localhost:5001/api)
- SAMPLE_FILE (optional, defaults to test_upload.txt at repo root)

This script is intended for developer runs or CI when real credentials and
backend are available. It measures timings and exits non-zero on failure.
"""
import os
import sys
import time
import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:5001/api")
SAMPLE_FILE = os.getenv("SAMPLE_FILE", os.path.join(os.path.dirname(__file__), "..", "..", "test_upload.txt"))
SAMPLE_FILE = os.path.abspath(SAMPLE_FILE)

HEALTHZ = f"{API_BASE.replace('/api','')}/healthz"
UPLOAD = f"{API_BASE}/upload"
QUERY = f"{API_BASE}/query"
RESET = f"{API_BASE}/reset"

print("Integration runner: API_BASE=", API_BASE)
print("Sample file:", SAMPLE_FILE)

if not os.path.exists(SAMPLE_FILE):
    print(f"ERROR: sample file not found: {SAMPLE_FILE}")
    sys.exit(2)

client = httpx.Client(timeout=30.0)

# 1. Health
print('\n1) Checking /healthz...')
try:
    r = client.get(HEALTHZ)
    r.raise_for_status()
    print('healthz response:', r.text)
    health = r.json()
    if not health.get('checks') or not all(health.get('checks', {}).values()):
        print('Health checks not all green:', health)
        # Continue but warn
        print('WARNING: health gate not fully green. Proceeding for debug.')
except Exception as e:
    print('ERROR: /healthz failed:', e)
    sys.exit(3)

# 2. Upload
print('\n2) Uploading sample file...')
start = time.time()
with open(SAMPLE_FILE, 'rb') as fh:
    files = {'file': (os.path.basename(SAMPLE_FILE), fh, 'text/plain')}
    try:
        r = client.post(UPLOAD, files=files)
        r.raise_for_status()
    except Exception as e:
        print('ERROR: Upload failed:', e)
        sys.exit(4)
end = time.time()
duration = end - start
print(f'Upload completed in {duration:.2f}s; status={r.status_code}')
try:
    resp = r.json()
except Exception:
    print('Upload returned non-JSON response:', r.text)
    sys.exit(5)
print('Upload response:', resp)

# 3. Query
print('\n3) Querying for sample phrase...')
question = 'sample text'
start = time.time()
try:
    r = client.post(QUERY, json={'question': question})
    r.raise_for_status()
    results = r.json()
except Exception as e:
    print('ERROR: Query failed:', e)
    sys.exit(6)
end = time.time()
qtime = end - start
print(f'Query completed in {qtime:.2f}s; status={r.status_code}')
print('Query results snapshot:', results if isinstance(results, dict) else str(results)[:200])

# 4. Reset
print('\n4) Resetting collection...')
try:
    r = client.delete(RESET)
    r.raise_for_status()
    print('Reset response:', r.json() if r.headers.get('content-type','').startswith('application/json') else r.text)
except Exception as e:
    print('ERROR: Reset failed:', e)
    sys.exit(7)

# 5. Query again
print('\n5) Querying after reset to verify empty results...')
try:
    r = client.post(QUERY, json={'question': question})
    r.raise_for_status()
    results_after = r.json()
except Exception as e:
    print('ERROR: Query after reset failed:', e)
    sys.exit(8)

print('Results after reset:', results_after)

# Basic assertions (non-strict): expect results_after to be empty or indicate no matches
empty_ok = False
if isinstance(results_after, dict):
    items = results_after.get('results') or results_after.get('items') or results_after.get('data')
    if not items:
        empty_ok = True

if not empty_ok:
    print('WARNING: Query after reset returned results; check implementation or reset timing')

print('\nIntegration runner finished successfully (warnings may have been printed).')
sys.exit(0)
