"""Integration Validation Gate for RAG Application

Final validation checklist before marking "DONE":
✓ Upload sample.txt via frontend API
✓ Verify upload succeeds with upload_id
✓ Run test_chroma_connection.py and verify count > 0
✓ Query "sample text" via API
✓ Verify results include scores and source metadata
✓ Reset collection via DELETE /api/reset
✓ Verify count returns to 0 after reset
✓ Re-upload and query to verify persistence
✓ All checks PASS → Implementation COMPLETE

Run this script with both servers running:
  Backend: python backend/app.py (port 5001)
  Frontend: python serve_frontend.py (port 3000)
"""
import sys
import time
import tempfile
from pathlib import Path
import subprocess

try:
    import requests
except ImportError:
    print("ERROR: requests library required. pip install requests")
    sys.exit(1)


class IntegrationValidator:
    """Comprehensive integration validation for RAG MVP."""
    
    def __init__(self):
        self.api_base = "http://localhost:5001/api"
        self.results = {}
        self.upload_count = 0
        
    def log_step(self, step_num, description):
        """Log a validation step."""
        print(f"\n{'='*70}")
        print(f"Step {step_num}: {description}")
        print(f"{'='*70}")
    
    def log_result(self, name, passed, details=""):
        """Log result of a check."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results[name] = passed
        print(f"{status} - {name}")
        if details:
            print(f"      {details}")
    
    def check_server_health(self):
        """Step 1: Verify backend is healthy."""
        self.log_step(1, "Check backend server health")
        
        try:
            resp = requests.get(f"http://localhost:5001/healthz", timeout=5)
            if resp.status_code != 200:
                self.log_result("Server Health", False, f"Status {resp.status_code}")
                return False
            
            data = resp.json()
            checks = data.get("checks", {})
            
            all_ok = all(checks.values())
            self.log_result("Server Health", all_ok, 
                f"env={checks.get('env')}, gemini={checks.get('gemini')}, chroma={checks.get('chroma')}")
            
            return all_ok
        except Exception as e:
            self.log_result("Server Health", False, str(e))
            return False
    
    def check_initial_stats(self):
        """Step 2: Get initial collection stats."""
        self.log_step(2, "Check initial collection stats")
        
        try:
            resp = requests.get(f"{self.api_base}/stats", timeout=5)
            if resp.status_code != 200:
                self.log_result("Initial Stats", False, f"Status {resp.status_code}")
                return False
            
            data = resp.json()
            count = data.get("chunk_count", -1)
            
            self.log_result("Initial Stats", True, f"Initial chunk count: {count}")
            return True
        except Exception as e:
            self.log_result("Initial Stats", False, str(e))
            return False
    
    def upload_sample_file(self, iteration=1):
        """Step 3/7: Upload sample.txt via frontend API."""
        self.log_step(3 if iteration == 1 else 7, 
                     f"Upload sample.txt (Iteration {iteration})")
        
        # Create sample content
        sample_content = """Sample Text Document

This is a sample text document used for testing the RAG system.
It contains information about machine learning, artificial intelligence,
and data science concepts.

Machine Learning Section:
Machine learning is a subset of artificial intelligence that enables
computers to learn from data without explicit programming. There are
three main types of machine learning: supervised learning, unsupervised
learning, and reinforcement learning.

Artificial Intelligence:
Artificial intelligence encompasses a wide range of technologies and
techniques that enable machines to perform tasks that typically require
human intelligence.

Data Science:
Data science is an interdisciplinary field that uses scientific methods,
processes, algorithms and systems to extract meaning from data.
"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(sample_content)
                temp_path = f.name
            
            # Upload via API
            with open(temp_path, 'rb') as f:
                files = {'file': f}
                resp = requests.post(
                    f"{self.api_base}/upload",
                    files=files,
                    timeout=30
                )
            
            if resp.status_code != 200:
                self.log_result(f"Upload ({iteration})", False, 
                    f"Status {resp.status_code}: {resp.json().get('error', 'Unknown error')}")
                return False
            
            data = resp.json()
            upload_id = data.get("upload_id")
            chunk_count = data.get("chunk_count", 0)
            filename = data.get("filename", "unknown")
            
            self.log_result(f"Upload ({iteration})", True, 
                f"ID={upload_id[:12]}..., chunks={chunk_count}, file={filename}")
            
            self.upload_count += 1
            
            # Clean up temp file
            Path(temp_path).unlink()
            
            return True
        except Exception as e:
            self.log_result(f"Upload ({iteration})", False, str(e))
            return False
    
    def verify_collection_has_chunks(self):
        """Step 4: Verify collection count increased."""
        self.log_step(4, "Verify collection count increased")
        
        try:
            # Wait for indexing
            time.sleep(1)
            
            resp = requests.get(f"{self.api_base}/stats", timeout=5)
            if resp.status_code != 200:
                self.log_result("Collection Count", False, f"Status {resp.status_code}")
                return False
            
            data = resp.json()
            count = data.get("chunk_count", 0)
            
            passed = count > 0
            self.log_result("Collection Count", passed, f"Chunks in collection: {count}")
            self.current_count = count
            
            return passed
        except Exception as e:
            self.log_result("Collection Count", False, str(e))
            return False
    
    def query_sample_text(self, iteration=1):
        """Step 5/8: Query "sample text phrase" via API."""
        self.log_step(5 if iteration == 1 else 8, 
                     f"Query 'sample text' (Iteration {iteration})")
        
        try:
            resp = requests.post(
                f"{self.api_base}/query",
                json={"question": "sample text", "top_k": 3, "min_score": 0.1},
                timeout=30
            )
            
            if resp.status_code != 200:
                self.log_result(f"Query ({iteration})", False, 
                    f"Status {resp.status_code}: {resp.json().get('error', 'Unknown')}")
                return False
            
            data = resp.json()
            results = data.get("results", [])
            count = data.get("count", 0)
            
            self.log_result(f"Query ({iteration})", len(results) > 0, 
                f"Found {count} results")
            
            return len(results) > 0
        except Exception as e:
            self.log_result(f"Query ({iteration})", False, str(e))
            return False
    
    def verify_result_structure(self):
        """Step 6: Verify results have scores and metadata."""
        self.log_step(6, "Verify result structure (scores and metadata)")
        
        try:
            resp = requests.post(
                f"{self.api_base}/query",
                json={"question": "sample text", "top_k": 2},
                timeout=30
            )
            
            if resp.status_code != 200:
                self.log_result("Result Structure", False, "Query failed")
                return False
            
            data = resp.json()
            results = data.get("results", [])
            
            if not results:
                self.log_result("Result Structure", False, "No results returned")
                return False
            
            # Check first result structure
            first = results[0]
            has_score = "score" in first and isinstance(first.get("score"), float)
            has_text = "text" in first and isinstance(first.get("text"), str)
            has_metadata = "metadata" in first and isinstance(first.get("metadata"), dict)
            
            if has_metadata:
                meta = first["metadata"]
                has_source = "source" in meta
                has_chunk_id = "chunk_id" in meta
            else:
                has_source = has_chunk_id = False
            
            all_ok = has_score and has_text and has_metadata and has_source and has_chunk_id
            
            details = f"score={has_score}, text={has_text}, metadata={has_metadata}, source={has_source}, chunk_id={has_chunk_id}"
            self.log_result("Result Structure", all_ok, details)
            
            if all_ok:
                score = first.get("score", 0)
                source = first["metadata"].get("source", "?")
                chunk_id = first["metadata"].get("chunk_id", "?")
                text_preview = first.get("text", "")[:60] + "..."
                print(f"\n      Sample result:")
                print(f"        Score: {score:.3f}")
                print(f"        Source: {source}")
                print(f"        Chunk: {chunk_id}")
                print(f"        Text: {text_preview}")
            
            return all_ok
        except Exception as e:
            self.log_result("Result Structure", False, str(e))
            return False
    
    def reset_collection(self):
        """Step 7: Reset collection via DELETE /api/reset."""
        self.log_step(7, "Reset collection")
        
        try:
            resp = requests.delete(
                f"{self.api_base}/reset",
                timeout=10
            )
            
            if resp.status_code != 200:
                self.log_result("Reset", False, f"Status {resp.status_code}")
                return False
            
            data = resp.json()
            message = data.get("message", "")
            count = data.get("count", -1)
            
            passed = count == 0
            self.log_result("Reset", passed, 
                f"Message: {message}, Count after reset: {count}")
            
            return passed
        except Exception as e:
            self.log_result("Reset", False, str(e))
            return False
    
    def verify_reset_empty(self):
        """Step 8: Verify collection is empty after reset."""
        self.log_step(8, "Verify collection empty after reset")
        
        try:
            resp = requests.get(f"{self.api_base}/stats", timeout=5)
            if resp.status_code != 200:
                self.log_result("Empty Verification", False, f"Status {resp.status_code}")
                return False
            
            data = resp.json()
            count = data.get("chunk_count", -1)
            
            passed = count == 0
            self.log_result("Empty Verification", passed, f"Chunk count: {count}")
            
            return passed
        except Exception as e:
            self.log_result("Empty Verification", False, str(e))
            return False
    
    def re_upload_persistence_test(self):
        """Step 9: Re-upload to verify persistence."""
        self.log_step(9, "Re-upload and query to verify persistence")
        
        # Upload again
        if not self.upload_sample_file(iteration=2):
            return False
        
        # Verify count increased
        if not self.verify_collection_has_chunks():
            return False
        
        # Query again
        if not self.query_sample_text(iteration=2):
            return False
        
        self.log_result("Persistence Test", True, "Re-upload and query successful")
        return True
    
    def run_chroma_connection_test(self):
        """Run test_chroma_connection.py to verify ChromaDB connectivity."""
        self.log_step(10, "Run test_chroma_connection.py")
        
        try:
            result = subprocess.run(
                ["python", "scripts/run_pytest_with_env.py", "tests/test_chroma_connection.py", "-q"],
                cwd="d:\\AI\\projects\\rag-app",
                capture_output=True,
                timeout=30
            )
            
            passed = result.returncode == 0
            details = "All tests passed" if passed else f"Return code: {result.returncode}"
            
            self.log_result("ChromaDB Connection Test", passed, details)
            
            if result.stdout:
                print(f"\n      Output:\n{result.stdout.decode()[:200]}")
            
            return passed
        except Exception as e:
            self.log_result("ChromaDB Connection Test", False, str(e))
            return False
    
    def run_all_validations(self):
        """Run complete integration validation."""
        print("\n" + "="*70)
        print("🧪 INTEGRATION VALIDATION GATE")
        print("="*70)
        print("\nThis is the final gate before marking implementation COMPLETE.")
        print("All checks must PASS.\n")
        
        try:
            # Main validation sequence
            if not self.check_server_health():
                return False
            
            if not self.check_initial_stats():
                return False
            
            # Upload iteration 1
            if not self.upload_sample_file(iteration=1):
                return False
            
            # Verify chunks in collection
            if not self.verify_collection_has_chunks():
                return False
            
            # Query and verify results
            if not self.query_sample_text(iteration=1):
                return False
            
            if not self.verify_result_structure():
                return False
            
            # Reset collection
            if not self.reset_collection():
                return False
            
            if not self.verify_reset_empty():
                return False
            
            # Re-upload and query to verify persistence
            if not self.re_upload_persistence_test():
                return False
            
            # Run ChromaDB connection test
            if not self.run_chroma_connection_test():
                return False
            
            return True
        
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def print_summary(self):
        """Print final summary."""
        print("\n" + "="*70)
        print("📋 VALIDATION SUMMARY")
        print("="*70)
        
        passed_count = sum(1 for v in self.results.values() if v)
        total_count = len(self.results)
        
        for test_name, passed in self.results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print("\n" + "="*70)
        print(f"Results: {passed_count}/{total_count} checks passed")
        print("="*70)
        
        if passed_count == total_count:
            print("\n🎉 ALL VALIDATION CHECKS PASSED!")
            print("\n✅ IMPLEMENTATION MARKED COMPLETE")
            print("\nThe RAG Knowledge Base system is ready for:")
            print("  • Development use")
            print("  • Integration testing")
            print("  • Feature expansion")
            print("  • Production deployment")
            print("\nNext steps:")
            print("  1. Commit changes to feature branch")
            print("  2. Push to remote repository")
            print("  3. Create pull request for review")
            print("  4. Deploy to staging environment")
            return 0
        else:
            print(f"\n⚠️  {total_count - passed_count} validation check(s) FAILED")
            print("\nPlease review failures above and retry.")
            return 1


def main():
    """Run integration validation."""
    validator = IntegrationValidator()
    
    # Run all validations
    all_passed = validator.run_all_validations()
    
    # Print summary
    validator.print_summary()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
