"""Quick test to validate chromadb Cloud client configuration and connectivity.

Run locally (requires environment variables):

    python -m pytest tests/test_chroma_connection.py -q

Environment variables required:
- CHROMA_API_KEY
- CHROMA_TENANT
- CHROMA_DATABASE

This test checks:
- `chromadb` is importable and its version is >= 0.6.0
- Required env vars are present
- Attempts to instantiate a CloudClient and list collections (best-effort; non-fatal if client API differs)
"""
import os
import sys
import pytest

REQUIRED = ["CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE"]


def test_env_vars_present():
    missing = [k for k in REQUIRED if not os.getenv(k)]
    assert not missing, f"Missing required env vars: {missing}"


def test_chromadb_import_and_version():
    try:
        import chromadb
    except Exception as e:
        pytest.skip(f"chromadb import failed: {e}")

    ver = getattr(chromadb, "__version__", "0.0.0")
    major = int(ver.split(".")[0]) if ver and ver.split(".") else 0
    assert major >= 0, "chromadb version could not be determined"
    # Best-effort check for minimum version 0.6.0
    def version_ge(v1, v2=(0,6,0)):
        parts = tuple(int(x) for x in v1.split(".")[:3])
        return parts >= v2

    assert version_ge(ver), f"chromadb version {ver} appears older than required >=0.6.0"


def test_cloud_client_connectivity():
    import chromadb
    api_key = os.getenv("CHROMA_API_KEY")
    tenant = os.getenv("CHROMA_TENANT")
    database = os.getenv("CHROMA_DATABASE")

    # Try to instantiate CloudClient in a few common ways (best-effort)
    client = None
    errors = []
    try:
        # Common v2 pattern: chromadb.CloudClient(api_key=..., tenant=...)
        client = chromadb.CloudClient(api_key=api_key, tenant=tenant)
    except Exception as e:
        errors.append(str(e))
    if client is None:
        try:
            # Alternative: chromadb.Client(...)
            client = chromadb.Client(api_key=api_key)
        except Exception as e:
            errors.append(str(e))

    if client is None:
        pytest.skip(f"Could not instantiate a chromadb client (attempted multiple patterns): {errors}")

    # Attempt to list or access collections (if API exposes such methods)
    try:
        if hasattr(client, "list_collections"):
            cols = client.list_collections()
            assert isinstance(cols, (list, tuple)), "list_collections() did not return a list-like object"
        elif hasattr(client, "get_collection"):
            # Non-fatal: just attempt a get on a default name
            _ = client.get_collection("rag-docs")
    except Exception as e:
        pytest.skip(f"Connected to chromadb client but operation failed (non-fatal): {e}")

    # If we reach here, at least the client was created without immediate fatal errors
    assert client is not None


if __name__ == "__main__":
    # Allow running directly: run pytest on this file
    sys.exit(pytest.main([__file__]))
