Create a cloud-powered knowledge retrieval system where users can:
The system must allow users to:
- Upload text documents (.txt, .md, .pdf) via drag-and-drop UI
- Chunk documents locally and embed them using Gemini text-embedding-004
- Store vectors in ChromaDB Cloud (tenant configured via environment variable)
- Ask natural language questions embedded using the same Gemini model
- View top-K retrieved chunks with similarity scores and source metadata
- Reset the remote collection (clears ChromaDB Cloud collection only)
- See real-time status for upload, embedding, and cloud sync


Acceptance Criteria for MVP readiness:
- Health endpoint returns all green checks (env, gemini, chroma)
- Upload 1KB txt file completes in <3s including embedding and cloud sync
- Query returns results with scores in <2s
- Reset clears collection (verified by subsequent empty query)
- Frontend correctly points to backend API (no 501/404 errors)
- No hardcoded credentials in committed code
