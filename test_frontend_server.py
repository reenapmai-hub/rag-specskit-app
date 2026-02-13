"""Quick test to verify frontend is serving."""
import requests
import time

time.sleep(2)

print("Testing frontend HTTP server...")
try:
    # Test root
    r = requests.get('http://localhost:3000/', timeout=5)
    print(f"GET / : {r.status_code}")
    print(f"  Has 'RAG': {'RAG' in r.text}")
    print(f"  Size: {len(r.text)} bytes")
    
    # Test index.html
    r = requests.get('http://localhost:3000/index.html', timeout=5)
    print(f"GET /index.html : {r.status_code}")
    print(f"  Has 'RAG Document Search': {'RAG Document Search' in r.text}")
    print(f"  Has 'uploadZone': {'uploadZone' in r.text}")
    print(f"  Has 'API_BASE': {'API_BASE' in r.text}")
    print(f"  Size: {len(r.text)} bytes")
    
    if r.status_code == 200 and 'RAG Document Search' in r.text:
        print("\n✅ Frontend is serving correctly!")
    else:
        print("\n⚠️  Frontend response may be incomplete")
        
except Exception as e:
    print(f"❌ Error testing frontend: {e}")
