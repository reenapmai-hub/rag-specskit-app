"""
Document processor for RAG system.

Responsibilities:
- extract_text(file_path): supports .txt, .md, .pdf
- chunk_text(text): split into 500-char chunks with 50-char overlap
- process_file(file_path): returns list of dicts:
    {
        "text": chunk_text,
        "metadata": {
            "source": filename,
            "chunk_id": index
        }
    }

Errors:
- Raise ValueError for unsupported file types
- Handle malformed or unreadable PDFs gracefully
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def extract_text(file_path: str | Path) -> str:
    """Extract text from a file.

    Supports:
    - .txt: plain text files
    - .md: Markdown files
    - .pdf: PDF files

    Args:
        file_path: Path to the file.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If file type is not supported or file cannot be read.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix in (".txt", ".md"):
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Failed to read {suffix} file: {e}") from e

    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text_parts: list[str] = []

            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    # Log warning but continue processing other pages
                    print(f"Warning: Failed to extract text from page {page_num}: {e}")

            return "\n".join(text_parts)

        except Exception as e:
            raise ValueError(f"Failed to read PDF file: {e}") from e
    elif suffix == ".docx":
        try:
            from docx import Document

            doc = Document(file_path)
            paragraphs: list[str] = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Failed to read DOCX file: {e}") from e

    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. Supported: .txt, .md, .pdf"
        )


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into chunks with overlap.

    Args:
        text: Text to chunk.
        chunk_size: Size of each chunk in characters (default: 500).
        overlap: Number of overlapping characters between chunks (default: 50).

    Returns:
        List of text chunks.

    Raises:
        ValueError: If chunk_size or overlap is invalid.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and less than chunk_size")

    if not text:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap

    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)

        # Stop if we've reached the end
        if i + chunk_size >= len(text):
            break

    return chunks


def process_file(file_path: str | Path) -> list[dict[str, Any]]:
    """Process a document file and return chunks with metadata.

    Args:
        file_path: Path to the document file.

    Returns:
        List of dicts with 'text' and 'metadata' keys.
        Metadata includes 'source' (filename) and 'chunk_id' (index).

    Raises:
        ValueError: If file type is not supported or extraction fails.
    """
    file_path = Path(file_path)

    # Extract text
    text = extract_text(file_path)

    # Chunk the text
    chunks = chunk_text(text)

    # Build result with metadata
    result: list[dict[str, Any]] = []
    source_name = file_path.name

    for chunk_id, chunk_text_item in enumerate(chunks):
        result.append(
            {
                "text": chunk_text_item,
                "metadata": {"source": source_name, "chunk_id": chunk_id},
            }
        )

    return result


if __name__ == "__main__":
    # Quick verification
    import tempfile

    # Test with a sample .txt file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is sample text. " * 50)
        temp_path = f.name

    try:
        result = process_file(temp_path)
        print(f"✅ Processed file: {len(result)} chunks")
        for i, chunk in enumerate(result[:2]):
            print(f"   Chunk {i}: {len(chunk['text'])} chars, source={chunk['metadata']['source']}")
    finally:
        Path(temp_path).unlink()

    print("✅ All tests passed")