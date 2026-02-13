"""
ChromaDB Cloud client for RAG system.

Responsibilities:
- Connect to ChromaDB Cloud using credentials from environment:
    CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE
- get_or_create_collection():
    - connects to collection named 'rag-docs'
- upsert_chunks(chunks):
    - accepts list of:
        {
            "text": str,
            "metadata": dict
        }
    - embeds text via embeddings.embed_texts
    - upserts into ChromaDB Cloud with ids and metadata
- query_similar(question, top_k=5):
    - embeds question via embeddings.embed_texts
    - queries ChromaDB Cloud
    - returns results with text, metadata, and similarity scores

Constraints:
- Must use ChromaDB v2 Cloud API (chromadb.CloudClient)
- No local persistence (cloud is source of truth)
- Fail fast if credentials missing
"""
from __future__ import annotations

import hashlib
import os
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from . import embeddings


COLLECTION_NAME = "rag-docs"

def load_credentials() -> dict[str, str]:
    """Load and validate ChromaDB Cloud credentials from environment.

    Raises:
        ValueError: If any required credential is missing.

    Returns:
        Dict with keys: api_key, tenant, database
    """
    required = ["CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE"]
    creds: dict[str, str] = {}

    for key in required:
        value = os.getenv(key, "").strip()
        if not value:
            raise ValueError(
                f"Missing required credential: {key}. "
                "Please set in .env or environment variables."
            )
        creds[key] = value

    return {
        "api_key": creds["CHROMA_API_KEY"],
        "tenant": creds["CHROMA_TENANT"],
        "database": creds["CHROMA_DATABASE"],
    }


def create_client() -> chromadb.CloudClient:
    """Create and return a ChromaDB Cloud client.

    Raises:
        ValueError: If credentials are missing or client creation fails.

    Returns:
        chromadb.CloudClient instance.
    """
    creds = load_credentials()

    try:
        client = chromadb.CloudClient(
            api_key=creds["api_key"],
            tenant=creds["tenant"],
            database=creds["database"],
        )
        return client
    except Exception as e:
        raise ValueError(f"Failed to create ChromaDB Cloud client: {e}") from e


def get_or_create_collection(client: chromadb.CloudClient) -> Collection:
    """Get or create the 'rag-docs' collection.

    Args:
        client: ChromaDB Cloud client.

    Returns:
        The collection object.

    Raises:
        RuntimeError: If collection operations fail.
    """
    try:
        # Use the built-in get_or_create_collection method
        # Omit metadata to avoid '_type' errors in ChromaDB Cloud
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
        )
        return collection
    except Exception as e:
        raise RuntimeError(f"Failed to get or create collection '{COLLECTION_NAME}': {e}") from e


def generate_chunk_id(source: str, chunk_id: int) -> str:
    """Generate a unique ID for a chunk.

    Args:
        source: Source filename
        chunk_id: Chunk index

    Returns:
        Unique ID string.
    """
    return hashlib.sha256(f"{source}:{chunk_id}".encode()).hexdigest()[:16]


def upsert_chunks(
    client: chromadb.CloudClient,
    collection: Collection,
    chunks: list[dict[str, Any]],
) -> int:
    """Embed and upsert chunks into ChromaDB Cloud.

    Args:
        client: ChromaDB Cloud client (for informational purposes).
        collection: ChromaDB collection.
        chunks: List of dicts with 'text' and 'metadata' keys.

    Returns:
        Number of chunks upserted.

    Raises:
        ValueError: If chunks format is invalid.
        RuntimeError: If embedding or upsert fails.
    """
    if not chunks:
        return 0

    # Validate chunk format
    for chunk in chunks:
        if "text" not in chunk or "metadata" not in chunk:
            raise ValueError("Each chunk must have 'text' and 'metadata' keys")

    # Extract texts and generate IDs
    texts = [chunk["text"] for chunk in chunks]
    ids: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for chunk in chunks:
        source = chunk["metadata"].get("source", "unknown")
        chunk_id = chunk["metadata"].get("chunk_id", 0)
        ids.append(generate_chunk_id(source, chunk_id))
        # Ensure all metadata values are strings to avoid ChromaDB '_type' errors
        metadata = {
            "source": str(source),
            "chunk_id": str(chunk_id),
        }
        metadatas.append(metadata)

    # Embed all texts using Gemini
    try:
        embeddings_list = embeddings.embed_texts(texts)
    except Exception as e:
        raise RuntimeError(f"Failed to embed chunks: {e}") from e

    # Upsert into ChromaDB
    try:
        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings_list,
            metadatas=metadatas,
        )
        return len(chunks)
    except Exception as e:
        raise RuntimeError(f"Failed to upsert chunks to ChromaDB: {e}") from e


def query_similar(
    collection: Collection,
    question: str,
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    """Query ChromaDB for similar documents.

    Args:
        collection: ChromaDB collection.
        question: Query question/text.
        top_k: Number of top results to return.

    Returns:
        List of dicts with 'text', 'metadata', and 'score' keys.

    Raises:
        ValueError: If question is empty.
        RuntimeError: If embedding or query fails.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")

    # Embed the question
    try:
        question_embeddings = embeddings.embed_texts([question])
        question_embedding = question_embeddings[0]
    except Exception as e:
        raise RuntimeError(f"Failed to embed question: {e}") from e

    # Query ChromaDB
    try:
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=top_k,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to query ChromaDB: {e}") from e

    # Format results
    formatted_results: list[dict[str, Any]] = []

    if results and results.get("documents") and len(results["documents"]) > 0:
        docs = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for i, doc in enumerate(docs):
            # Convert distance to similarity score (1 - distance)
            # ChromaDB uses cosine distance by default
            score = 1 - distances[i] if i < len(distances) else 1.0

            formatted_results.append(
                {
                    "text": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "score": score,
                }
            )

    # Filter by minimum score
    if min_score and min_score > 0:
        formatted_results = [r for r in formatted_results if r.get("score", 0) >= float(min_score)]

    # Normalize sources and collect unique sources
    for r in formatted_results:
        md = r.setdefault("metadata", {})
        src = md.get("source", "")
        md["source"] = str(src).strip() if src is not None else ""

    unique_sources = set(r.get("metadata", {}).get("source", "") for r in formatted_results if r.get("metadata"))

    # If multiple sources are present, deduplicate to best chunk per source.
    # If only a single source is present, keep top-k chunks from that source.
    if len(unique_sources) > 1:
        deduped: dict[str, dict[str, Any]] = {}
        for r in formatted_results:
            src = r.get("metadata", {}).get("source", "")
            if not src:
                continue
            prev = deduped.get(src)
            if prev is None or r.get("score", 0) > prev.get("score", 0):
                deduped[src] = r

        results_list = list(deduped.values())
    else:
        # Single source — return the highest-scoring chunks up to top_k
        results_list = formatted_results

    # Sort by score descending and limit to top_k
    results_list.sort(key=lambda x: x.get("score", 0), reverse=True)

    return results_list[:top_k]


if __name__ == "__main__":
    # Quick verification test
    try:
        print("Testing ChromaDB Cloud client...")

        # Load credentials
        creds = load_credentials()
        print(f"✅ Credentials loaded: tenant={creds['tenant']}, database={creds['database']}")

        # Create client
        client = create_client()
        print("✅ CloudClient created")

        # Get or create collection
        collection = get_or_create_collection(client)
        print(f"✅ Collection '{COLLECTION_NAME}' accessible (count: {collection.count()})")

        print("✅ All tests passed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import sys

        sys.exit(1)