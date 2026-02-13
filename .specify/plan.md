System architecture:
- Backend: Python Flask REST API (stateless, no local storage)
* Port: 5001 (avoid macOS conflicts with 5000)
* Dependencies: chromadb>=0.6.0, numpy<2, Flask==3.0.0, httpx>=0.27.0
- Vector Store: ChromaDB Cloud (tenant c15dd4dc-0b07-4ab4-a933-7d29a489dc7b,
database Magic-Test)
* Client: chromadb.CloudClient (v2 API)
- Embeddings: Google Gemini text-embedding-004 via AI Platform API
- Credentials: .env file with GOOGLE_API_KEY and ChromaDB CloudClient config
- Chunking: Local text splitting (500 chars, 50 overlap) before API calls
- API Endpoints:
* POST /api/upload - Supports .txt, .md, .pdf (PDF parsed via PyPDF2 or pdfplumber), calls Gemini embedding API, upserts to
ChromaDB Cloud
* POST /api/query - accepts question, embeds via Gemini, queries ChromaDB Cloud,
returns top-5 chunks
* DELETE /api/reset - deletes ChromaDB Cloud collection and recreates empty
* GET /healthz - validates env vars, Gemini reachability, ChromaDB Cloud connection
- Frontend: Static HTML/CSS/JS (fetch API for all calls)
* API base: window.API_BASE || "http://localhost:5001/api"
- No local persistence (Flask session-only, ChromaDB Cloud is source of truth)
- Error handling: API quota limits (Gemini), network timeouts (ChromaDB Cloud),
malformed PDFs
- Testing: test_chroma_connection.py script to validate credentials before full
implementation
- Deployment verification: curl /healthz must return all checks=true before frontend test