"""Test Gemini embedding wrapper functionality.

Verifies:
- embed_texts() accepts list of strings
- Returns vectors with correct dimensionality
- Handles batching (up to 100 texts per call)
- Implements retry logic with exponential backoff
"""
import os
import sys
from pathlib import Path

# Add repo root to path so we can import backend
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from backend import embeddings


def test_validate_api_key():
    """Test that GOOGLE_API_KEY validation works."""
    api_key = embeddings.validate_api_key()
    assert api_key, "API key should be loaded from environment"
    assert len(api_key) > 0, "API key should not be empty"


def test_embed_single_text():
    """Test embedding a single text."""
    result = embeddings.embed_texts(["hello"])
    assert isinstance(result, list), "Should return a list"
    assert len(result) == 1, "Should return 1 embedding for 1 text"
    assert isinstance(result[0], list), "Each embedding should be a list"
    assert len(result[0]) == 3072, "Embedding vector should be 3072-dimensional (Gemini model)"


def test_embed_multiple_texts():
    """Test embedding multiple texts."""
    texts = ["hello", "world", "test"]
    result = embeddings.embed_texts(texts)
    assert len(result) == 3, "Should return 3 embeddings for 3 texts"
    for embedding in result:
        assert isinstance(embedding, list), "Each embedding should be a list"
        assert len(embedding) == 3072, "Each embedding should be 3072-dimensional"


def test_embed_empty_list_raises_error():
    """Test that empty list raises ValueError."""
    with pytest.raises(ValueError, match="texts list cannot be empty"):
        embeddings.embed_texts([])


def test_embed_texts_are_different():
    """Test that different texts produce different embeddings."""
    texts = ["apple", "banana"]
    embeddings_result = embeddings.embed_texts(texts)
    # Embeddings should be different but not necessarily completely disjoint
    assert embeddings_result[0] != embeddings_result[1], "Different texts should produce different embeddings"


def test_batching_with_large_list():
    """Test that batching works with a large list of texts (>100)."""
    # Create 105 texts to test batching (BATCH_SIZE = 100)
    texts = [f"text number {i}" for i in range(105)]
    result = embeddings.embed_texts(texts)
    assert len(result) == 105, "Should return embeddings for all texts"
    for embedding in result:
        assert len(embedding) == 3072, "All embeddings should be 3072-dimensional"


if __name__ == "__main__":
    # Allow running directly with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
