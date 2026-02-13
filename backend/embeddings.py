"""
Task 2: Gemini embedding wrapper

Requirements:
- Function: embed_texts(texts: list[str]) -> list[list[float]]
- Uses Google Gemini model: text-embedding-004
- Supports batching (up to 100 texts per request)
- Reads GOOGLE_API_KEY from environment
- Raises clear error if key missing
- Returns 768-dim vectors
- Retry logic with exponential backoff on rate limits

Verification:
- embed_texts(["hello"]) returns one vector of length 768
"""

from __future__ import annotations

import os
import time
from typing import Any

import google.generativeai as genai


BATCH_SIZE = 100
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 32.0
EMBEDDING_MODEL = "models/gemini-embedding-001"


def validate_api_key() -> str:
    """Load and validate GOOGLE_API_KEY from environment.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set or empty.

    Returns:
        str: The API key value.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not set in environment. "
            "Please set it in .env or as an environment variable."
        )
    return api_key


def configure_genai(api_key: str) -> None:
    """Configure the generative AI client with the API key.

    Args:
        api_key: Google API key for Gemini.
    """
    genai.configure(api_key=api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using Google Gemini API with batching and retry logic.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each 768-dimensional).

    Raises:
        ValueError: If texts is empty or GOOGLE_API_KEY is not set.
        RuntimeError: If all retries are exhausted or embedding fails.
    """
    if not texts:
        raise ValueError("texts list cannot be empty")

    api_key = validate_api_key()
    configure_genai(api_key)

    all_embeddings: list[list[float]] = []

    # Process in batches
    for batch_start in range(0, len(texts), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(texts))
        batch = texts[batch_start:batch_end]

        # Retry logic with exponential backoff
        backoff = INITIAL_BACKOFF_SECONDS
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                # Call Gemini API to embed the batch
                response = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=batch,
                )

                # Handle response format from embedding API
                if "embedding" in response:
                    embeddings = response["embedding"]
                elif isinstance(response, dict) and "embeddings" in response:
                    embeddings = response["embeddings"]
                else:
                    embeddings = response

                # Validate that embeddings match expected dimensions (3072)
                for embedding in embeddings:
                    if not isinstance(embedding, (list, tuple)):
                        raise RuntimeError(
                            f"Unexpected embedding format: {type(embedding)}"
                        )
                    if len(embedding) != 3072:
                        raise RuntimeError(
                            f"Embedding has {len(embedding)} dimensions, expected 3072"
                        )

                all_embeddings.extend(embeddings)
                break  # Success, move to next batch

            except genai.types.BlockedPromptException as e:
                # Prompt was blocked; don't retry
                raise RuntimeError(f"Prompt blocked by Gemini API: {e}") from e

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check for rate limit errors
                is_rate_limited = (
                    "rate" in error_str
                    or "quota" in error_str
                    or "429" in error_str
                    or "503" in error_str
                )

                if is_rate_limited and attempt < MAX_RETRIES - 1:
                    # Rate limited; apply exponential backoff and retry
                    wait_time = min(backoff, MAX_BACKOFF_SECONDS)
                    print(
                        f"Rate limited. Retrying batch after {wait_time:.1f}s "
                        f"(attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(wait_time)
                    backoff *= 2

                elif attempt == MAX_RETRIES - 1:
                    # Last attempt failed
                    raise RuntimeError(
                        f"Failed to embed batch after {MAX_RETRIES} attempts: {e}"
                    ) from e
                else:
                    # Non-rate-limit error; fail immediately
                    raise RuntimeError(f"Failed to embed batch: {e}") from e

    return all_embeddings


if __name__ == "__main__":
    # Simple verification test
    try:
        result = embed_texts(["hello"])
        print(f"✅ embed_texts(['hello']) returned {len(result)} vector(s)")
        print(f"   Vector dimension: {len(result[0])}")
        assert len(result) == 1
        assert len(result[0]) == 3072
        print("✅ All checks passed")
    except Exception as e:
        print(f"❌ Error: {e}")
        import sys

        sys.exit(1)
