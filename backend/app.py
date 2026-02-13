"""
Task 5: Build Flask API routes

Routes:
- POST /api/upload:
    file → extract → chunk → embed (Gemini) → upsert (ChromaDB Cloud)
- POST /api/query:
    {question} → embed (Gemini) → search (ChromaDB Cloud) → return chunks with scores
- DELETE /api/reset:
    delete ChromaDB Cloud collection, recreate empty
- GET /healthz:
    check Gemini API key valid, ChromaDB Cloud reachable (return JSON with checks)

Server:
- Runs on port 5001
- Start with: FLASK_APP=backend.app flask run --port 5001

Verify:
- curl http://localhost:5001/healthz returns:
  {"checks": {"chroma": true, "gemini": true, "env": true}}
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request
from flask_cors import CORS


from . import chroma_client, document_processor, embeddings


app = Flask(__name__)
CORS(app) 

# Global client and collection cache
_client: chroma_client.chromadb.CloudClient | None = None
_collection: chroma_client.Collection | None = None


def get_client_and_collection() -> tuple[chroma_client.chromadb.CloudClient, chroma_client.Collection]:
    """Get or create ChromaDB client and collection (cached at module level)."""
    global _client, _collection

    if _client is None:
        _client = chroma_client.create_client()

    if _collection is None:
        _collection = chroma_client.get_or_create_collection(_client)

    return _client, _collection


@app.route("/healthz", methods=["GET"])
def healthz() -> tuple[dict[str, object], int]:
    """Health check endpoint.

    Returns:
        JSON with checks: {chroma, gemini, env}
    """
    checks: dict[str, bool] = {}

    # Check environment variables
    checks["env"] = all(
        os.getenv(key)
        for key in ["CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE", "GOOGLE_API_KEY"]
    )

    # Check ChromaDB connectivity
    try:
        client, collection = get_client_and_collection()
        _ = collection.count()
        checks["chroma"] = True
    except Exception:
        checks["chroma"] = False

    # Check Gemini API key
    try:
        _ = embeddings.validate_api_key()
        checks["gemini"] = True
    except Exception:
        checks["gemini"] = False

    return jsonify({"checks": checks}), 200


@app.route("/api/stats", methods=["GET"])
def stats() -> tuple[dict[str, object], int]:
    """Return simple stats from ChromaDB collection.

    Returns:
        JSON with `chunk_count`.
    """
    try:
        client, collection = get_client_and_collection()
        count = collection.count()
        return jsonify({"chunk_count": count}), 200
    except Exception as e:
        return jsonify({"error": f"Stats failed: {e}"}), 500


@app.route("/api/upload", methods=["POST"])
def upload_file() -> tuple[dict[str, object], int]:
    """Upload and process a document.

    Expects multipart/form-data with 'file' field.

    Returns:
        JSON with upload_id and chunk count.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        # Save file to temp location
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(file.filename).suffix,
        ) as tmp:
            file.save(tmp.name)
            temp_path = tmp.name

        # Process document
        chunks = document_processor.process_file(temp_path)

        if not chunks:
            return jsonify({"error": "No text extracted from file"}), 400

        # Upsert into ChromaDB
        client, collection = get_client_and_collection()
        upserted_count = chroma_client.upsert_chunks(client, collection, chunks)

        upload_id = str(uuid4())

        return (
            jsonify(
                {
                    "upload_id": upload_id,
                    "filename": file.filename,
                    "chunk_count": upserted_count,
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": f"File processing error: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Upload failed: {e}"}), 500

    finally:
        # Clean up temp file
        try:
            Path(temp_path).unlink()
        except Exception:
            pass


@app.route("/api/query", methods=["POST"])
def query() -> tuple[dict[str, object], int]:
    """Query similar documents.

    Expects JSON: {"question": "..."}

    Returns:
        JSON with results list.
    """
    data = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        client, collection = get_client_and_collection()
        data = request.get_json() or {}
        top_k = int(data.get("top_k", 5))
        min_score = float(data.get("min_score", 0.0))

        results = chroma_client.query_similar(collection, question, top_k=top_k, min_score=min_score)

        # Extra server-side safety: enforce min_score and top_k
        try:
            filtered = [r for r in results if r.get("score", 0) >= float(min_score)]
        except Exception:
            filtered = results

        filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
        final = filtered[:top_k]

        # Debug info: include counts to verify filtering is applied
        return (
            jsonify(
                {
                    "question": question,
                    "results": final,
                    "count": len(final),
                    "debug": {
                        "requested_top_k": top_k,
                        "requested_min_score": min_score,
                        "returned_before_filter": len(results),
                        "returned_after_filter": len(final),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Query failed: {e}"}), 500


@app.route("/api/reset", methods=["DELETE"])
def reset() -> tuple[dict[str, object], int]:
    """Reset collection (delete and recreate).

    Returns:
        JSON confirmation.
    """
    global _client, _collection

    try:
        client, collection = get_client_and_collection()

        # Delete collection
        try:
            client.delete_collection(name=chroma_client.COLLECTION_NAME)
        except Exception:
            # Collection may not exist
            pass

        # Reset cache and recreate
        _client = client
        _collection = chroma_client.get_or_create_collection(client)

        return (
            jsonify(
                {
                    "message": f"Collection '{chroma_client.COLLECTION_NAME}' reset",
                    "count": _collection.count(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Reset failed: {e}"}), 500


@app.errorhandler(404)
def not_found(error: Exception) -> tuple[dict[str, str], int]:
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error: Exception) -> tuple[dict[str, str], int]:
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
