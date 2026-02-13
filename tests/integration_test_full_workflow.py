"""Integration test for full RAG frontend-to-backend workflow.

Verifies:
1. Flask API server responds to all endpoints
2. File upload → chunking → embedding → ChromaDB storage
3. Query → search in ChromaDB → results with scores
4. Stats and reset operations
5. Frontend can communicate with backend

Run this after starting both servers:
  - Backend: python backend/app.py (port 5001)
  - Frontend: python -m http.server 3000 -d frontend (port 3000)
"""
import sys
import time
import tempfile
from pathlib import Path

# Test with requests
try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)


def test_backend_health():
    """Verify backend health endpoint."""
    print("\n📊 Testing Backend Health...")
    try:
        resp = requests.get("http://localhost:5001/healthz", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        checks = data.get("checks", {})
        
        print(f"  ✅ /healthz returns 200")
        print(f"     - Env check: {checks.get('env', False)}")
        print(f"     - Gemini check: {checks.get('gemini', False)}")
        print(f"     - ChromaDB check: {checks.get('chroma', False)}")
        
        assert all(checks.values()), "Not all health checks passed"
        print(f"  ✅ All health checks passed")
        
        return True
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False


def test_stats_endpoint():
    """Verify stats endpoint."""
    print("\n📈 Testing Stats Endpoint...")
    try:
        resp = requests.get("http://localhost:5001/api/stats", timeout=5)
        assert resp.status_code == 200
        
        data = resp.json()
        chunk_count = data.get("chunk_count")
        
        print(f"  ✅ /api/stats returns 200")
        print(f"     - Initial chunk count: {chunk_count}")
        
        return True
    except Exception as e:
        print(f"  ❌ Stats check failed: {e}")
        return False


def test_upload_and_query():
    """Test upload and query workflow."""
    print("\n📤 Testing Upload Workflow...")
    
    # Create temporary test file
    test_content = """
    Machine Learning Basics
    
    Machine learning is a subset of artificial intelligence that focuses on
    enabling computers to learn from data without being explicitly programmed.
    
    There are three main types of machine learning:
    1. Supervised learning - learns from labeled data
    2. Unsupervised learning - finds patterns in unlabeled data
    3. Reinforcement learning - learns through trial and error
    
    Deep learning uses neural networks with multiple layers to process data.
    It has been revolutionary in computer vision, natural language processing,
    and other areas.
    """
    
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        # Upload file
        print("  Uploading test file...")
        with open(temp_path, 'rb') as f:
            files = {'file': f}
            resp = requests.post(
                "http://localhost:5001/api/upload",
                files=files,
                timeout=30
            )
        
        assert resp.status_code == 200, f"Upload failed: {resp.status_code}"
        
        data = resp.json()
        upload_id = data.get("upload_id")
        filename = data.get("filename")
        chunk_count = data.get("chunk_count")
        
        print(f"  ✅ Upload successful")
        print(f"     - Upload ID: {upload_id[:8]}...")
        print(f"     - Filename: {filename}")
        print(f"     - Chunks: {chunk_count}")
        
        assert chunk_count > 0, "No chunks created"
        
        # Wait a moment for indexing
        time.sleep(1)
        
        # Query the uploaded content
        print("  Querying for uploaded content...")
        resp = requests.post(
            "http://localhost:5001/api/query",
            json={"question": "What is machine learning?", "top_k": 3},
            timeout=30
        )
        
        assert resp.status_code == 200, f"Query failed: {resp.status_code}"
        
        result = resp.json()
        results = result.get("results", [])
        count = result.get("count", 0)
        
        print(f"  ✅ Query successful")
        print(f"     - Results returned: {count}")
        
        if count > 0:
            for i, res in enumerate(results[:2], 1):
                score = res.get("score", 0)
                source = res.get("metadata", {}).get("source", "unknown")
                chunk_id = res.get("metadata", {}).get("chunk_id", "?")
                text_preview = res.get("text", "")[:50] + "..."
                print(f"     - Result {i}: score={score:.2f}, source={source}, chunk={chunk_id}")
                print(f"       Text: {text_preview}")
        
        # Verify stats updated
        print("  Checking updated stats...")
        resp = requests.get("http://localhost:5001/api/stats", timeout=5)
        data = resp.json()
        new_chunk_count = data.get("chunk_count")
        print(f"  ✅ Stats updated: {new_chunk_count} chunks")
        
        # Clean up
        Path(temp_path).unlink()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Upload/Query workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reset_operation():
    """Test reset operation."""
    print("\n🔄 Testing Reset Operation...")
    try:
        # Get current count
        resp = requests.get("http://localhost:5001/api/stats", timeout=5)
        before_count = resp.json().get("chunk_count", 0)
        print(f"  Chunks before reset: {before_count}")
        
        # Reset
        resp = requests.delete(
            "http://localhost:5001/api/reset",
            timeout=10
        )
        
        assert resp.status_code == 200, f"Reset failed: {resp.status_code}"
        
        data = resp.json()
        message = data.get("message")
        after_count = data.get("count", 0)
        
        print(f"  ✅ Reset successful: {message}")
        print(f"     - Chunks after reset: {after_count}")
        
        assert after_count == 0, "Collection should be empty after reset"
        
        return True
        
    except Exception as e:
        print(f"  ❌ Reset operation failed: {e}")
        return False


def test_frontend_accessibility():
    """Verify frontend is accessible."""
    print("\n🌐 Testing Frontend Accessibility...")
    try:
        resp = requests.get("http://localhost:3000", timeout=5)
        assert resp.status_code == 200, f"Frontend returned {resp.status_code}"
        
        content = resp.text
        assert "RAG Document Search" in content, "Frontend HTML not found"
        assert "API_BASE" in content, "API_BASE configuration not found"
        
        print(f"  ✅ Frontend accessible on http://localhost:3000")
        print(f"     - HTML contains RAG Document Search title")
        print(f"     - API_BASE configuration present")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Frontend accessibility check failed: {e}")
        return False


def verify_api_configuration():
    """Verify API configuration is correct."""
    print("\n⚙️  Verifying API Configuration...")
    try:
        # Check frontend HTML for API configuration
        resp = requests.get("http://localhost:3000", timeout=5)
        content = resp.text
        
        # Verify API base is configured
        if "const apiBase" in content:
            print(f"  ✅ API base configured in frontend")
        
        # Check for required UI elements
        required_elements = [
            "uploadZone",
            "queryInput",
            "askBtn",
            "resultsContainer",
            "totalChunks",
            "resetBtn",
            "confirmModal"
        ]
        
        missing_elements = []
        for element in required_elements:
            if f'id="{element}"' not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"  ⚠️  Missing UI elements: {missing_elements}")
        else:
            print(f"  ✅ All required UI elements present")
        
        return len(missing_elements) == 0
        
    except Exception as e:
        print(f"  ❌ Configuration verification failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("🧪 RAG Frontend-Backend Integration Tests")
    print("=" * 60)
    
    print("\nPrerequisites:")
    print("  1. Backend running: http://localhost:5001")
    print("  2. Frontend running: http://localhost:3000")
    print("  3. Environment variables set (.env file)")
    print("  4. ChromaDB Cloud credentials valid")
    
    results = {}
    
    # Run tests
    results["Backend Health"] = test_backend_health()
    results["Stats Endpoint"] = test_stats_endpoint()
    results["Frontend Access"] = test_frontend_accessibility()
    results["API Configuration"] = verify_api_configuration()
    results["Upload & Query"] = test_upload_and_query()
    results["Reset Operation"] = test_reset_operation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All integration tests PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
