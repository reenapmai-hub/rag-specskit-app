"""Unit tests for ChromaDB Cloud operations.

Verifies:
- get_or_create_collection() connects to 'rag-docs' collection
- upsert_chunks() embeds text via Gemini and uploads to ChromaDB Cloud with metadata
- query_similar() embeds question and retrieves similar chunks with scores
- Collection starts empty (count=0) after creation/reset
"""
import sys
from pathlib import Path
from unittest import mock

# Add repo root to path so we can import backend
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import pytest
from backend import chroma_client, embeddings


def create_mock_embedding(text: str) -> list[float]:
    """Create a deterministic mock embedding for testing.
    
    Uses hash of text to generate a consistent vector for unit tests.
    Returns a 3072-dimensional vector (Gemini embedding size).
    """
    import hashlib
    hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
    # Generate 3072-dimensional vector using hash seeding
    vector = []
    for i in range(3072):
        seed = hash_value + i
        # Use deterministic pseudo-random generator
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        value = (seed / 0x7fffffff) * 2 - 1  # Normalize to [-1, 1]
        vector.append(value)
    return vector


@pytest.fixture
def chroma_client_instance():
    """Fixture to create a ChromaDB Cloud client for testing."""
    client = chroma_client.create_client()
    yield client


@pytest.fixture
def collection(chroma_client_instance):
    """Fixture to create/get a test collection and reset it."""
    collection_obj = chroma_client.get_or_create_collection(chroma_client_instance)
    
    # Clear collection before test
    try:
        chroma_client_instance.delete_collection(name=chroma_client.COLLECTION_NAME)
    except Exception:
        pass
    
    # Create fresh collection
    collection_obj = chroma_client.get_or_create_collection(chroma_client_instance)
    
    yield collection_obj
    
    # Cleanup after test
    try:
        chroma_client_instance.delete_collection(name=chroma_client.COLLECTION_NAME)
    except Exception:
        pass


class TestChromaClient:
    """Tests for chromadb client creation."""

    def test_load_credentials(self):
        """Test that credentials are loaded from environment."""
        creds = chroma_client.load_credentials()
        assert isinstance(creds, dict), "load_credentials should return a dict"
        assert "api_key" in creds, "Credentials should have api_key"
        assert "tenant" in creds, "Credentials should have tenant"
        assert "database" in creds, "Credentials should have database"
        assert creds["api_key"], "API key should not be empty"
        assert creds["tenant"], "Tenant should not be empty"
        assert creds["database"], "Database should not be empty"

    def test_create_client(self):
        """Test CloudClient creation."""
        client = chroma_client.create_client()
        assert client is not None, "create_client should return a client object"
        # Verify it's a CloudClient by checking for expected methods
        assert hasattr(client, "get_or_create_collection"), "Client should have get_or_create_collection method"


class TestGetOrCreateCollection:
    """Tests for get_or_create_collection() function."""

    def test_get_or_create_collection_returns_collection(self, chroma_client_instance):
        """Test that get_or_create_collection returns a collection object."""
        collection = chroma_client.get_or_create_collection(chroma_client_instance)
        assert collection is not None, "Collection should be returned"
        assert hasattr(collection, "count"), "Collection should have count method"

    def test_collection_name_is_correct(self, chroma_client_instance):
        """Test that collection is created with correct name."""
        collection = chroma_client.get_or_create_collection(chroma_client_instance)
        assert collection.name == chroma_client.COLLECTION_NAME, \
            f"Collection name should be '{chroma_client.COLLECTION_NAME}'"

    def test_collection_starts_empty(self, collection):
        """Test that a new/reset collection has count=0."""
        count = collection.count()
        assert count == 0, f"Empty collection should have count=0, got {count}"


class TestUpsertChunks:
    """Tests for upsert_chunks() function."""

    @mock.patch('backend.embeddings.embed_texts')
    def test_upsert_single_chunk(self, mock_embed, chroma_client_instance, collection):
        """Test upserting a single chunk."""
        # Mock embedding function to avoid API calls
        mock_embed.return_value = [create_mock_embedding("This is a test chunk.")]
        
        chunks = [
            {
                "text": "This is a test chunk.",
                "metadata": {"source": "test.txt", "chunk_id": 0}
            }
        ]

        count = chroma_client.upsert_chunks(chroma_client_instance, collection, chunks)
        assert count == 1, "Should upsert 1 chunk"
        
        # Verify count increased
        collection_count = collection.count()
        assert collection_count >= 1, f"Collection count should be >= 1 after upsert, got {collection_count}"

    @mock.patch('backend.embeddings.embed_texts')
    def test_upsert_multiple_chunks(self, mock_embed, chroma_client_instance, collection):
        """Test upserting multiple chunks."""
        # Mock embedding function for all 3 chunks
        texts = [
            "Chunk one with some content.",
            "Chunk two with different content.",
            "Chunk three from a different document."
        ]
        mock_embed.return_value = [create_mock_embedding(t) for t in texts]
        
        chunks = [
            {
                "text": texts[0],
                "metadata": {"source": "doc1.txt", "chunk_id": 0}
            },
            {
                "text": texts[1],
                "metadata": {"source": "doc1.txt", "chunk_id": 1}
            },
            {
                "text": texts[2],
                "metadata": {"source": "doc2.txt", "chunk_id": 0}
            }
        ]

        count = chroma_client.upsert_chunks(chroma_client_instance, collection, chunks)
        assert count == 3, "Should upsert 3 chunks"
        
        collection_count = collection.count()
        assert collection_count >= 3, f"Collection count should be >= 3, got {collection_count}"

    @mock.patch('backend.embeddings.embed_texts')
    def test_upsert_chunks_with_metadata(self, mock_embed, chroma_client_instance, collection):
        """Test that metadata is correctly stored."""
        # Mock embedding
        mock_embed.return_value = [create_mock_embedding("Test text with metadata.")]
        
        chunks = [
            {
                "text": "Test text with metadata.",
                "metadata": {"source": "sample.md", "chunk_id": 42}
            }
        ]

        chroma_client.upsert_chunks(chroma_client_instance, collection, chunks)
        
        # Query to verify metadata was stored
        results = collection.get()
        assert results["metadatas"], "Collection should have metadata"
        
        # Check metadata content
        metadata = results["metadatas"][0]
        assert metadata.get("source") == "sample.md", "Source metadata should be preserved"
        assert metadata.get("chunk_id") == "42", "Chunk ID metadata should be preserved (as string)"

    def test_upsert_empty_chunks_list(self, chroma_client_instance, collection):
        """Test upserting an empty list."""
        chunks = []
        count = chroma_client.upsert_chunks(chroma_client_instance, collection, chunks)
        assert count == 0, "Upserting empty list should return 0"

    def test_upsert_invalid_chunks_format(self, chroma_client_instance, collection):
        """Test that invalid chunk format raises ValueError."""
        invalid_chunks = [
            {"text": "Missing metadata"}  # Missing 'metadata' key
        ]

        with pytest.raises(ValueError, match="Each chunk must have 'text' and 'metadata' keys"):
            chroma_client.upsert_chunks(chroma_client_instance, collection, invalid_chunks)


class TestQuerySimilar:
    """Tests for query_similar() function."""

    def test_query_empty_collection(self, collection):
        """Test querying an empty collection."""
        results = chroma_client.query_similar(collection, "test question")
        assert isinstance(results, list), "query_similar should return a list"
        assert len(results) == 0, "Empty collection should return no results"

    @mock.patch('backend.embeddings.embed_texts')
    def test_query_with_results(self, mock_embed, chroma_client_instance, collection):
        """Test querying collection with data."""
        # Setup: upsert test data
        texts = [
            "The quick brown fox jumps over the lazy dog.",
            "Dogs are loyal companions and best friends.",
            "Machine learning is a subset of artificial intelligence."
        ]
        mock_embed.return_value = [create_mock_embedding(t) for t in texts]
        
        chunks = [
            {
                "text": texts[0],
                "metadata": {"source": "animals.txt", "chunk_id": 0}
            },
            {
                "text": texts[1],
                "metadata": {"source": "pets.txt", "chunk_id": 0}
            },
            {
                "text": texts[2],
                "metadata": {"source": "ai.txt", "chunk_id": 0}
            }
        ]

        chroma_client.upsert_chunks(chroma_client_instance, collection, chunks)

        # Test: query for dogs
        mock_embed.return_value = [create_mock_embedding("dogs")]
        results = chroma_client.query_similar(collection, "dogs", top_k=2)
        assert isinstance(results, list), "query_similar should return a list"
        assert len(results) <= 2, "Should respect top_k parameter"
        
        # Results should have required fields
        if len(results) > 0:
            first_result = results[0]
            assert "text" in first_result, "Result should have 'text' field"
            assert "metadata" in first_result, "Result should have 'metadata' field"
            assert "score" in first_result, "Result should have 'score' field"
            assert isinstance(first_result["score"], float), "Score should be a float"
            assert 0 <= first_result["score"] <= 1, "Score should be between 0 and 1"

    @mock.patch('backend.embeddings.embed_texts')
    def test_query_top_k_parameter(self, mock_embed, chroma_client_instance, collection):
        """Test that top_k parameter is respected."""
        # Upsert 5 chunks
        texts = [f"Content chunk {i} with some text." for i in range(5)]
        mock_embed.return_value = [create_mock_embedding(t) for t in texts]
        
        chunks = [
            {
                "text": texts[i],
                "metadata": {"source": f"doc{i}.txt", "chunk_id": 0}
            }
            for i in range(5)
        ]

        chroma_client.upsert_chunks(chroma_client_instance, collection, chunks)

        # Query with top_k=2
        mock_embed.return_value = [create_mock_embedding("content")]
        results = chroma_client.query_similar(collection, "content", top_k=2)
        assert len(results) <= 2, "Should return at most top_k results"

    def test_query_empty_question(self, collection):
        """Test that empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            chroma_client.query_similar(collection, "")

    @mock.patch('backend.embeddings.embed_texts')
    def test_query_with_min_score(self, mock_embed, chroma_client_instance, collection):
        """Test querying with minimum score filter."""
        mock_embed.return_value = [create_mock_embedding("This is a sample document.")]
        
        chunks = [
            {
                "text": "This is a sample document.",
                "metadata": {"source": "sample.txt", "chunk_id": 0}
            }
        ]

        chroma_client.upsert_chunks(chroma_client_instance, collection, chunks)

        # Query with different patterns
        mock_embed.return_value = [create_mock_embedding("sample")]
        results_no_filter = chroma_client.query_similar(collection, "sample", top_k=5, min_score=0.0)
        
        mock_embed.return_value = [create_mock_embedding("random text")]
        results_with_filter = chroma_client.query_similar(collection, "random text", top_k=5, min_score=0.5)
        
        # Results with filter should be a subset (or equal) to results without filter
        assert len(results_with_filter) <= len(results_no_filter), \
            "Filtered results should have fewer or equal items than unfiltered"


class TestChunkIdGeneration:
    """Tests for chunk ID generation."""

    def test_generate_chunk_id_consistency(self):
        """Test that chunk IDs are generated consistently for same input."""
        id1 = chroma_client.generate_chunk_id("file.txt", 0)
        id2 = chroma_client.generate_chunk_id("file.txt", 0)
        assert id1 == id2, "Same input should generate same chunk ID"

    def test_generate_chunk_id_uniqueness(self):
        """Test that different inputs generate different chunk IDs."""
        id1 = chroma_client.generate_chunk_id("file1.txt", 0)
        id2 = chroma_client.generate_chunk_id("file2.txt", 0)
        id3 = chroma_client.generate_chunk_id("file1.txt", 1)
        
        assert id1 != id2, "Different files should generate different IDs"
        assert id1 != id3, "Different chunk IDs should generate different IDs"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
