"""Unit tests for document processor (extract_text, chunk_text, process_file).

Verifies:
- extract_text() handles .txt, .md, .pdf
- chunk_text() splits into 500-char chunks with 50-char overlap
- process_file() returns list of {text, metadata: {source, chunk_id}}
"""
import sys
from pathlib import Path

# Add repo root to path so we can import backend
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
import pytest
from backend import document_processor


class TestExtractText:
    """Tests for extract_text() function."""

    def test_extract_text_from_txt(self):
        """Test extracting text from a .txt file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("This is sample text.\nSecond line.")
            temp_path = f.name

        try:
            text = document_processor.extract_text(temp_path)
            assert isinstance(text, str), "extract_text should return a string"
            assert "This is sample text" in text, "Extracted text should contain the written content"
            assert "Second line" in text, "Extracted text should contain all lines"
        finally:
            Path(temp_path).unlink()

    def test_extract_text_from_md(self):
        """Test extracting text from a .md (Markdown) file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Heading\n\nThis is markdown content.")
            temp_path = f.name

        try:
            text = document_processor.extract_text(temp_path)
            assert "# Heading" in text, "Markdown formatting should be preserved"
            assert "This is markdown content" in text, "Extracted text should contain content"
        finally:
            Path(temp_path).unlink()

    def test_extract_text_file_not_found(self):
        """Test that extract_text raises ValueError for non-existent files."""
        with pytest.raises(ValueError, match="File not found"):
            document_processor.extract_text("/nonexistent/path/file.txt")

    def test_extract_text_unsupported_file_type(self):
        """Test that extract_text raises ValueError for unsupported file types."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                document_processor.extract_text(temp_path)
        finally:
            Path(temp_path).unlink()


class TestChunkText:
    """Tests for chunk_text() function."""

    def test_chunk_text_basic(self):
        """Test basic text chunking with default parameters."""
        # Create text longer than chunk size (500 chars)
        text = "a" * 1200  # 1200 characters total

        chunks = document_processor.chunk_text(text)
        assert isinstance(chunks, list), "chunk_text should return a list"
        assert len(chunks) > 0, "Should produce at least one chunk"

        # Each chunk should be <= CHUNK_SIZE (500)
        for chunk in chunks:
            assert len(chunk) <= document_processor.CHUNK_SIZE, f"Chunk size {len(chunk)} exceeds limit {document_processor.CHUNK_SIZE}"
            assert chunk.strip(), "Chunks should not be empty after stripping"

    def test_chunk_text_with_overlap(self):
        """Test that chunks overlap correctly."""
        # Create text with recognizable patterns to verify overlap
        text = "The quick brown fox jumps over the lazy dog. " * 20  # ~900 chars

        chunks = document_processor.chunk_text(
            text,
            chunk_size=document_processor.CHUNK_SIZE,
            overlap=document_processor.CHUNK_OVERLAP,
        )

        assert len(chunks) >= 2, "Text longer than chunk_size should produce multiple chunks"

        # Check that consecutive chunks have overlap
        if len(chunks) >= 2:
            first_chunk = chunks[0]
            second_chunk = chunks[1]

            # The end of the first chunk should overlap with the start of the second
            overlap_region = first_chunk[-document_processor.CHUNK_OVERLAP :]
            assert overlap_region in second_chunk or second_chunk[:document_processor.CHUNK_OVERLAP] in first_chunk, \
                f"Chunks should overlap; first_chunk end: {overlap_region[:20]}..., second_chunk start: {second_chunk[:20]}..."

    def test_chunk_text_small_text(self):
        """Test chunking text smaller than chunk size."""
        text = "Small text"
        chunks = document_processor.chunk_text(text)
        assert len(chunks) == 1, "Small text should produce one chunk"
        assert chunks[0] == text, "Small text should be returned as-is"

    def test_chunk_text_empty_text(self):
        """Test chunking empty text."""
        text = ""
        chunks = document_processor.chunk_text(text)
        assert chunks == [], "Empty text should produce empty chunk list"

    def test_chunk_text_invalid_parameters(self):
        """Test chunk_text with invalid parameters."""
        text = "sample text"

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            document_processor.chunk_text(text, chunk_size=0)

        with pytest.raises(ValueError, match="overlap must be non-negative"):
            document_processor.chunk_text(text, chunk_size=100, overlap=-1)

        with pytest.raises(ValueError, match="overlap must be non-negative"):
            document_processor.chunk_text(text, chunk_size=100, overlap=100)


class TestProcessFile:
    """Tests for process_file() function."""

    def test_process_file_txt(self):
        """Test processing a .txt file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            # Write enough text to produce multiple chunks
            content = "This is a test document. " * 50  # ~1250 chars
            f.write(content)
            temp_path = f.name

        try:
            result = document_processor.process_file(temp_path)

            assert isinstance(result, list), "process_file should return a list"
            assert len(result) > 0, "Should produce at least one chunk"

            # Check structure of each chunk
            for idx, chunk in enumerate(result):
                assert isinstance(chunk, dict), f"Chunk {idx} should be a dict"
                assert "text" in chunk, f"Chunk {idx} should have 'text' key"
                assert "metadata" in chunk, f"Chunk {idx} should have 'metadata' key"

                # Check metadata structure
                metadata = chunk["metadata"]
                assert "source" in metadata, f"Metadata {idx} should have 'source' key"
                assert "chunk_id" in metadata, f"Metadata {idx} should have 'chunk_id' key"
                assert metadata["chunk_id"] == idx, f"Chunk ID should match index {idx}"
                assert Path(temp_path).name in metadata["source"], f"Source should contain filename"

        finally:
            Path(temp_path).unlink()

    def test_process_file_chunk_count(self):
        """Test that chunk count matches expected value."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            # Create text with known length to predict chunk count
            # With CHUNK_SIZE=500 and OVERLAP=50, step is 450 per chunk
            content = "a" * 1350  # Should produce ~3 chunks
            f.write(content)
            temp_path = f.name

        try:
            result = document_processor.process_file(temp_path)
            # Expected chunks: ceil(1350 / 450) = 3
            assert len(result) >= 2, "1350 chars should produce at least 2 chunks"
            assert len(result) <= 4, "1350 chars should produce at most 4 chunks"
        finally:
            Path(temp_path).unlink()

    def test_process_file_unsupported_type(self):
        """Test process_file with unsupported file type."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                document_processor.process_file(temp_path)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
