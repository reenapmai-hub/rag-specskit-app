# research.md — Phase 0 Research

**Feature**: 001-add-rag-kb
**Date**: 2026-02-13

This document resolves open questions (NEEDS CLARIFICATION) and records design decisions for Phase 1.

---

## Decisions

1. Authentication for MVP (REQUIRES ANSWER)

- Decision: Option B — Unauthenticated POC with gated integration tests using ephemeral credentials.
- Rationale: Prioritizes fast iteration and minimal UX friction for developers and reviewers. Integration tests that exercise real credentials will run only in CI with ephemeral secrets; local dev quickstart will use developer-provided env vars.
- Alternatives evaluated: Require auth (adds token issuance and UX) — rejected for POC speed; Optional auth (adds complexity) — postponed to later phase.
- Implications: Production deployments MUST add authentication; README and quickstart must clearly document the security trade-offs.

2. Chunking parameters

- Decision: Client-side chunking with 500 characters per chunk and 50-character overlap (approx conservative token estimate). Configurable via frontend constants.
- Rationale: Simple to implement in-browser; keeps network payloads small and aligns with backend expectations.

3. Embedding provider and model

- Decision: Gemini `text-embedding-004` (per spec). Use HTTP requests via `httpx` from backend; do not persist API keys in source.
- Rationale: Matches user requirement for managed embeddings; reduces local compute.

4. ChromaDB Cloud usage

- Decision: Use `chromadb.CloudClient` (v2) and tenant `c15dd4dc-0b07-4ab4-a933-7d29a489dc7b`. Ensure `chromadb>=0.6.0` is in requirements and `numpy<2.0.0` pin.
- Rationale: Cloud-first constitutional requirement and compatibility with v2 API.

5. Performance & retries

- Decision: Implement simple exponential backoff for embedding API calls (max 3 retries) and separate timeout for ChromaDB writes. Capture timings for CI assertions.

6. Observability & transparency

- Decision: Return retrieval metadata with each query (chunk id, doc id, similarity score, retrieval rank) and expose a `debug` flag the frontend can toggle to fetch full retrieval traces.

7. Integration testing approach

- Decision: Provide `tests/integration/test_upload_query_reset.py` which:
  - Requires `CI_GEMINI_KEY` and `CI_CHROMA_CONFIG` set in CI.
  - Calls `/healthz` to validate connectivity.
  - Uploads a 1KB sample file via `/api/upload` and asserts ingestion time <3s.
  - Performs `/api/query` and asserts results and latency <2s.
  - Calls `/api/reset` and asserts subsequent query returns empty results.
- Rationale: Satisfies constitution gate that final sign-off requires a real-credentials run.

---

## Open Items

- RATIFICATION_DATE for the constitution must be filled by project lead.
- Confirm whether OCR support for PDFs is desired in a follow-up feature.

---

## Outcome

All explicit NEEDS CLARIFICATION items in the spec have been resolved for the POC, selecting an unauthenticated POC mode with gated CI integration tests. This enables Phase 1 design artifacts to be produced without blocking on larger security design decisions.
