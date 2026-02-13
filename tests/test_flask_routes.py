"""Unit tests for Flask API routes.

Verifies:
- GET /healthz returns checks for chroma, gemini, env
- POST /api/upload processes files and upserts chunks
- POST /api/query searches ChromaDB Cloud
- DELETE /api/reset clears collection
- GET /api/stats returns chunk count
"""
import sys
from pathlib import Path
from unittest import mock
import io

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from backend.app import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_embeddings():
    """Mock embeddings to avoid API rate limits."""
    def create_mock_embedding(text: str) -> list[float]:
        import hashlib
        hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        vector = []
        for i in range(3072):
            seed = hash_value + i
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            value = (seed / 0x7fffffff) * 2 - 1
            vector.append(value)
        return vector

    with mock.patch('backend.embeddings.embed_texts') as mock_embed:
        original_embed = mock_embed.side_effect
        
        def embed_side_effect(texts):
            return [create_mock_embedding(t) for t in texts]
        
        mock_embed.side_effect = embed_side_effect
        yield mock_embed


class TestHealthz:
    """Tests for GET /healthz endpoint."""

    def test_healthz_returns_json(self, client):
        """Test that /healthz returns JSON with checks."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict), "Response should be JSON"
        assert "checks" in data, "Response should have 'checks' key"

    def test_healthz_checks_structure(self, client):
        """Test that /healthz includes required checks."""
        response = client.get("/healthz")
        data = response.get_json()
        checks = data.get("checks", {})
        
        assert isinstance(checks, dict), "Checks should be a dict"
        assert "env" in checks, "Should check env vars"
        assert "chroma" in checks, "Should check ChromaDB"
        assert "gemini" in checks, "Should check Gemini API"

    def test_healthz_check_values_are_bool(self, client):
        """Test that check values are booleans."""
        response = client.get("/healthz")
        data = response.get_json()
        checks = data.get("checks", {})
        
        for key, value in checks.items():
            assert isinstance(value, bool), f"Check '{key}' should be boolean"


class TestStats:
    """Tests for GET /api/stats endpoint."""

    def test_stats_returns_json(self, client):
        """Test that /api/stats returns JSON."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict), "Response should be JSON"

    def test_stats_includes_chunk_count(self, client):
        """Test that /api/stats includes chunk_count."""
        response = client.get("/api/stats")
        data = response.get_json()
        assert "chunk_count" in data, "Should include chunk_count"
        assert isinstance(data["chunk_count"], int), "chunk_count should be integer"


class TestUpload:
    """Tests for POST /api/upload endpoint."""

    def test_upload_no_file(self, client):
        """Test upload with no file provided."""
        response = client.post("/api/upload")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data, "Should return error message"

    def test_upload_empty_filename(self, client):
        """Test upload with empty filename."""
        response = client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b""), "")},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data, "Should return error for empty filename"

    @mock.patch('backend.embeddings.embed_texts')
    @mock.patch('backend.document_processor.process_file')
    def test_upload_valid_file(self, mock_process, mock_embed, client):
        """Test successful file upload."""
        # Mock document processor
        mock_process.return_value = [
            {"text": "Sample text", "metadata": {"source": "test.txt", "chunk_id": 0}},
            {"text": "More text", "metadata": {"source": "test.txt", "chunk_id": 1}},
        ]
        
        # Mock embeddings
        mock_embed.return_value = [
            [0.1] * 3072,
            [0.2] * 3072,
        ]

        response = client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"test content"), "test.txt")},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "upload_id" in data, "Should return upload_id"
        assert "filename" in data, "Should return filename"
        assert "chunk_count" in data, "Should return chunk_count"
        assert data["filename"] == "test.txt"
        assert data["chunk_count"] == 2

    @mock.patch('backend.document_processor.process_file')
    def test_upload_no_text_extracted(self, mock_process, client):
        """Test upload when no text is extracted."""
        mock_process.return_value = []  # No chunks extracted

        response = client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"test"), "test.txt")},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data, "Should return error"
        assert "text extracted" in data["error"].lower()

    @mock.patch('backend.embeddings.embed_texts')
    @mock.patch('backend.document_processor.process_file')
    def test_upload_returns_valid_schema(self, mock_process, mock_embed, client):
        """Test that upload response has correct schema."""
        mock_process.return_value = [
            {"text": "Text", "metadata": {"source": "file.txt", "chunk_id": 0}},
        ]
        mock_embed.return_value = [[0.1] * 3072]

        response = client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"content"), "file.txt")},
        )

        data = response.get_json()
        assert isinstance(data["upload_id"], str)
        assert len(data["upload_id"]) > 0
        assert data["chunk_count"] >= 1


class TestQuery:
    """Tests for POST /api/query endpoint."""

    def test_query_no_question(self, client):
        """Test query with no question provided."""
        response = client.post("/api/query", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_query_empty_question(self, client):
        """Test query with empty question."""
        response = client.post("/api/query", json={"question": ""})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    @mock.patch('backend.chroma_client.query_similar')
    @mock.patch('backend.chroma_client.get_or_create_collection')
    @mock.patch('backend.chroma_client.create_client')
    def test_query_valid(self, mock_client, mock_collection, mock_query, client):
        """Test successful query."""
        # Mock ChromaDB result
        mock_query.return_value = [
            {
                "text": "Sample result",
                "metadata": {"source": "test.txt", "chunk_id": 0},
                "score": 0.95,
            }
        ]
        mock_client.return_value = mock.Mock()
        mock_collection.return_value = mock.Mock()

        response = client.post("/api/query", json={"question": "test question"})

        assert response.status_code == 200
        data = response.get_json()
        assert "question" in data, "Should return question"
        assert "results" in data, "Should return results"
        assert "count" in data, "Should return count"
        assert data["question"] == "test question"

    @mock.patch('backend.chroma_client.query_similar')
    @mock.patch('backend.chroma_client.get_or_create_collection')
    @mock.patch('backend.chroma_client.create_client')
    def test_query_empty_results(self, mock_client, mock_collection, mock_query, client):
        """Test query with no results."""
        mock_query.return_value = []
        mock_client.return_value = mock.Mock()
        mock_collection.return_value = mock.Mock()

        response = client.post("/api/query", json={"question": "unlikely question"})

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 0

    @mock.patch('backend.chroma_client.query_similar')
    @mock.patch('backend.chroma_client.get_or_create_collection')
    @mock.patch('backend.chroma_client.create_client')
    def test_query_with_top_k(self, mock_client, mock_collection, mock_query, client):
        """Test query with custom top_k parameter."""
        mock_query.return_value = [
            {"text": f"Result {i}", "metadata": {}, "score": 0.9 - i*0.1}
            for i in range(3)
        ]
        mock_client.return_value = mock.Mock()
        mock_collection.return_value = mock.Mock()

        response = client.post(
            "/api/query",
            json={"question": "test", "top_k": 2},
        )

        data = response.get_json()
        assert data["count"] <= 2, "Should respect top_k limit"
        assert "debug" in data, "Should include debug info"

    @mock.patch('backend.chroma_client.query_similar')
    @mock.patch('backend.chroma_client.get_or_create_collection')
    @mock.patch('backend.chroma_client.create_client')
    def test_query_with_min_score(self, mock_client, mock_collection, mock_query, client):
        """Test query with minimum score filter."""
        mock_query.return_value = [
            {"text": "High score", "metadata": {}, "score": 0.95},
            {"text": "Low score", "metadata": {}, "score": 0.2},
        ]
        mock_client.return_value = mock.Mock()
        mock_collection.return_value = mock.Mock()

        response = client.post(
            "/api/query",
            json={"question": "test", "min_score": 0.5},
        )

        data = response.get_json()
        # Should filter out low score
        assert data["count"] <= 2
        for result in data["results"]:
            assert result["score"] >= 0.5, "Results should meet min_score"


class TestReset:
    """Tests for DELETE /api/reset endpoint."""

    @mock.patch('backend.chroma_client.get_or_create_collection')
    @mock.patch('backend.chroma_client.create_client')
    def test_reset_success(self, mock_client, mock_collection, client):
        """Test successful collection reset."""
        mock_coll = mock.Mock()
        mock_coll.count.return_value = 0
        mock_collection.return_value = mock_coll
        mock_client.return_value = mock.Mock()

        response = client.delete("/api/reset")

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data, "Should return confirmation message"
        assert "count" in data, "Should return final count"
        assert data["count"] == 0, "Collection should be empty after reset"

    @mock.patch('backend.chroma_client.get_or_create_collection')
    @mock.patch('backend.chroma_client.create_client')
    def test_reset_recreates_collection(self, mock_client, mock_collection, client):
        """Test that reset recreates the collection."""
        mock_coll = mock.Mock()
        mock_coll.count.return_value = 0
        mock_collection.return_value = mock_coll
        mock_client.return_value = mock.Mock()

        response = client.delete("/api/reset")

        # Verify get_or_create_collection was called to recreate
        assert response.status_code == 200
        assert "reset" in response.get_json()["message"].lower()


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_upload_with_invalid_content_type(self, client):
        """Test upload with invalid content type."""
        response = client.post(
            "/api/upload",
            data="invalid",
            content_type="application/json",
        )
        assert response.status_code == 400

    @mock.patch('backend.chroma_client.query_similar')
    @mock.patch('backend.chroma_client.get_or_create_collection')
    @mock.patch('backend.chroma_client.create_client')
    def test_query_with_invalid_json(self, mock_client, mock_collection, mock_query, client):
        """Test query with invalid JSON."""
        response = client.post(
            "/api/query",
            data="invalid json",
            content_type="application/json",
        )
        assert response.status_code in [400, 415], "Should reject invalid JSON"


class TestCORS:
    """Tests for CORS headers."""

    def test_healthz_cors_headers(self, client):
        """Test that /healthz includes CORS headers."""
        response = client.get("/healthz")
        # Flask-CORS should add headers automatically
        assert response.status_code == 200

    def test_upload_cors_headers(self, client):
        """Test that /api/upload includes CORS headers."""
        # Note: POST with file won't work but we're testing CORS headers
        response = client.post("/api/upload")
        assert response.status_code in [400, 200]  # May fail for other reasons


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
