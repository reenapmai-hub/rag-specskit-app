"""Test Flask API endpoints."""
import requests
import json
import sys

base_url = 'http://localhost:5001'

try:
    # Test /healthz
    print('✓ Testing GET /healthz...')
    resp = requests.get(f'{base_url}/healthz', timeout=5)
    print(f'  Status: {resp.status_code}')
    data = resp.json()
    print(f'  Response: {json.dumps(data, indent=2)}')
    assert resp.status_code == 200, "Should return 200"
    assert 'checks' in data, "Should have 'checks' key"
    assert all(k in data['checks'] for k in ['chroma', 'gemini', 'env']), "Should have all checks"
    print()

    # Test /api/stats
    print('✓ Testing GET /api/stats...')
    resp = requests.get(f'{base_url}/api/stats', timeout=5)
    print(f'  Status: {resp.status_code}')
    data = resp.json()
    print(f'  Response: {json.dumps(data, indent=2)}')
    assert resp.status_code == 200, "Should return 200"
    assert 'chunk_count' in data, "Should have 'chunk_count' key"
    print()

    # Test /api/query (empty question - should fail)
    print('✓ Testing POST /api/query with empty question (should fail)...')
    resp = requests.post(f'{base_url}/api/query', json={'question': ''}, timeout=5)
    print(f'  Status: {resp.status_code}')
    data = resp.json()
    print(f'  Response: {json.dumps(data, indent=2)}')
    assert resp.status_code == 400, "Should return 400 for empty question"
    print()

    # Test /api/query without question - should fail
    print('✓ Testing POST /api/query without question (should fail)...')
    resp = requests.post(f'{base_url}/api/query', json={}, timeout=5)
    print(f'  Status: {resp.status_code}')
    data = resp.json()
    print(f'  Response: {json.dumps(data, indent=2)}')
    assert resp.status_code == 400, "Should return 400 when question missing"
    print()

    # Test /api/upload without file - should fail
    print('✓ Testing POST /api/upload without file (should fail)...')
    resp = requests.post(f'{base_url}/api/upload', timeout=5)
    print(f'  Status: {resp.status_code}')
    data = resp.json()
    print(f'  Response: {json.dumps(data, indent=2)}')
    assert resp.status_code == 400, "Should return 400 when file missing"
    print()

    # Test 404 error handling
    print('✓ Testing 404 error handling...')
    resp = requests.get(f'{base_url}/nonexistent', timeout=5)
    print(f'  Status: {resp.status_code}')
    data = resp.json()
    print(f'  Response: {json.dumps(data, indent=2)}')
    assert resp.status_code == 404, "Should return 404 for nonexistent route"
    print()

    print('✅ All API endpoint tests PASSED!')
    sys.exit(0)

except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
