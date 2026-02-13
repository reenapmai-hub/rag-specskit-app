0. Pre-flight checks
- Verify .env exists with all required keys (fail fast if missing)
- Create test_chroma_connection.py to validate tenant/database connectivity
- Run test script and ensure ✅ before proceeding
- Verify port 5001 is available (lsof -i :5001 returns empty)
1. Setup environment & credentials
- Install with exact versions: chromadb>=0.6.0, numpy<2, Flask==3.0.0, httpx>=0.27.0
- Create .env with actual credentials (not placeholders)
- Pin requirements.txt with tested versions
- Verify: python -c "import chromadb; print(chromadb.__version__)" shows >=0.6.0
2. Build Gemini embedding wrapper
- Function: embed_text(text_chunk) -> returns 768-dim vector from Gemini API
- Handles batching (Gemini allows up to 100 texts per request)
- Retry logic for rate limits (exponential backoff)
- Verify: test script calls embed_texts(['hello']) and gets 768-dim result
3. Create document processor
- extract_text(file) - handles .txt, .md, .pdf
- chunk_text(text) - splits into 500-char chunks with 50-char overlap
- Returns list of {text, metadata: {source, chunk_id}}
- Verify: unit test with sample.txt produces expected chunk count
4. Implement ChromaDB Cloud operations
- Use chromadb.CloudClient(api_key=..., tenant=..., database=...) for v2 API
- get_or_create_collection() - connects to 'rag-docs' collection in Magic-Test database
- upsert_chunks(chunks) - embeds via Gemini, uploads to ChromaDB Cloud with
metadata
- query_similar(question, top_k=5) - embeds question, retrieves from cloud, returns
with scores
- Verify: test_chroma_connection.py shows collection exists with count=0
5. Build Flask API routes
- POST /api/upload: file → extract → chunk → embed (Gemini) → upsert (ChromaDB
Cloud)
- POST /api/query: {question} → embed (Gemini) → search (ChromaDB Cloud) →
return chunks with scores
- DELETE /api/reset: delete ChromaDB Cloud collection, recreate empty
- GET /healthz: check Gemini API key valid, ChromaDB Cloud reachable (return
JSON with checks)
- Start server on port 5001 with: FLASK_APP=backend.app flask run --port 5001
- Verify: curl http://localhost:5001/healthz returns {"checks": {"chroma": true, "gemini":
true, "env": true}}
6. Create frontend UI
- File upload zone with progress bar (shows "Embedding via Gemini..." status)
- Query input with "Ask" button
- Results panel: displays chunks with similarity scores, source file, chunk position
- Collection stats widget: shows total chunks in cloud, last sync time
- Reset button with confirmation modal
- API base configured: const apiBase = window.API_BASE || "http://localhost:5001/
api";
- Serve via: python -m http.server 3000 in frontend/
- Verify: Open http://localhost:3000, upload test file, query returns results
7. Integration validation (gate before "done")
- Upload sample.txt via frontend
- Verify upload shows success message with upload_id
- Run test_chroma_connection.py, confirm count > 0
- Query "sample text phrase" via frontend
- Verify results show scores and source metadata
- Click Reset, confirm collection count returns to 0
- Re-upload and query to verify persistence
- All checks pass → mark implementation complete