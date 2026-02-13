---
description: "Tasks for feature 001-add-rag-kb: Cloud RAG Knowledge Base"
---
# Regenerated: 2026-02-13

# Tasks: 001-add-rag-kb — Cloud RAG Knowledge Base

**Input**: Design docs from `specs/001-add-rag-kb/` (`spec.md`, `plan.md`, `research.md`)
**Prerequisites**: Follow constitution gates (ChromaDB Cloud, Gemini embeddings, env secrets, chromadb>=0.6.0, numpy<2.0.0)

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 [P] Create `.env.example` at `.env.example` with keys: `GOOGLE_API_KEY`, `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE`, `PORT`
- [ ] T002 [P] Pin backend dependencies in `backend/requirements.txt` with versions: `chromadb>=0.6.0`, `numpy<2.0.0`, `Flask==3.0.0`, `httpx>=0.27.0`
- [ ] T003 Create `backend/.env` loader guidance in `backend/README.md` explaining env var usage and how to set ephemeral CI secrets
- [ ] T004 [P] Add a small helper script `scripts/check_port.ps1` to verify port `5001` availability on developer machines
- [ ] T005 [P] Add `.gitignore` rules to exclude `.env` and any local credentials at `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T006 Create `tests/test_chroma_connection.py` to validate ChromaDB Cloud client connectivity and collection access (uses env vars)
- [ ] T007 [P] Implement Chroma client utilities in `backend/chroma_client.py` with functions: `get_or_create_collection(collection_name='rag-docs')`, `delete_and_recreate_collection()`
- [ ] T008 [P] Implement Gemini embedding wrapper in `backend/embeddings.py` with function `embed_texts(texts: List[str]) -> List[List[float]]` including batching (100 per request) and exponential backoff
- [ ] T009 [P] Implement document processing utilities in `backend/document_processor.py`: `extract_text(file_path)` (txt/md/pdf) and `chunk_text(text, size=500, overlap=50)` returning list of `{text, metadata}`
- [ ] T010 Add environment validation in `backend/utils/env_check.py` used by `/healthz` and CI to assert presence of required env vars
- [ ] T011 [P] Add `scripts/test_chroma_connection_runner.py` to run `tests/test_chroma_connection.py` and exit non-zero on failure (used in gating)
- [ ] T012 Add `backend/requirements-locked.txt` (optional) after verifying versions locally with `pip freeze` for CI reproducibility

---

## Phase 3: User Story 1 - Upload & Index Documents (Priority: P1) 🎯 MVP

**Goal**: Accept user file uploads, perform client chunking, call Gemini embeddings, upsert vectors+metadata into ChromaDB Cloud, surface progress and cloud sync confirmation.

**Independent Test**: Upload a 1KB `.txt` file via the frontend and assert ingestion completes <3s and `tests/integration/test_upload_query_reset.py` records a successful upsert.

- [ ] T013 [US1] Implement `POST /api/upload` in `backend/app.py` that accepts file uploads and coordinates `backend/document_processor.py`, `backend/embeddings.py`, and `backend/chroma_client.py`
- [ ] T014 [US1] Add streaming/upload progress and embedding status events in `backend/app.py` logs and return an `upload_id` in the response
- [ ] T015 [P] [US1] Implement client-side upload and chunking helper in `frontend/upload.js` (or inline in `frontend/index.html`) showing progress and status messages
- [ ] T016 [US1] Add an integration test `tests/integration/test_upload.py` that posts sample.txt to `/api/upload` and asserts `200` with `upload_id`

---

## Phase 4: User Story 2 - Natural Language Query & Retrieval (Priority: P1)

**Goal**: Accept a question, embed via Gemini, query ChromaDB Cloud, and return top-5 chunks with similarity scores and metadata.

**Independent Test**: Call `POST /api/query` and verify top-5 results with similarity scores within 2s.

- [ ] T017 [US2] Implement `POST /api/query` in `backend/app.py` to embed question (use `backend/embeddings.py`) and query the ChromaDB collection via `backend/chroma_client.py`
- [ ] T018 [P] [US2] Implement results rendering in `frontend/results.js` (or inline) to display chunk text, similarity score, source filename, and chunk offsets
- [ ] T019 [US2] Add `tests/integration/test_query.py` to call `/api/query` against the ingested collection and assert results and scores
- [ ] T020 [P] [US2] Ensure query responses include retrieval metadata and optional `debug` trace controlled by a query param

---

## Phase 5: User Story 3 - Remote Reset of Collection (Priority: P2)

**Goal**: Provide a safe API to delete and recreate the ChromaDB Cloud collection for test isolation.

**Independent Test**: Call `DELETE /api/reset`, then call `/api/query` and assert empty results.

- [ ] T021 [US3] Implement `DELETE /api/reset` in `backend/app.py` which calls `backend/chroma_client.py` delete-and-recreate logic
- [ ] T022 [P] [US3] Add a Reset confirmation modal and button in `frontend/index.html` wired to the reset API
- [ ] T023 [US3] Add `tests/integration/test_reset.py` that calls `/api/reset` and verifies collection count is zero

---

## Phase 6: Health + Observability (Foundational)

**Goal**: Provide `/healthz` that validates env, Gemini access, and ChromaDB connectivity; make health gateable in CI.

- [ ] T024 Implement `GET /healthz` in `backend/app.py` that returns JSON: `{checks: {env: bool, gemini: bool, chroma: bool}, details: {...}}`
- [ ] T025 [P] Add timing capture for upload/query operations in `backend/app.py` and surface them in `/healthz` or logs for CI assertions

---

## Phase 7: Frontend polish & UX

- [ ] T026 [P] Update `frontend/index.html` UI to show collection stats widget (calls `/api/collection_stats` or `/healthz`)
- [ ] T027 [P] Add client-side config `frontend/config.js` to read `window.API_BASE || "http://localhost:5001/api"`
- [ ] T028 [P] Ensure frontend served by `python -m http.server 3000` can access backend with CORS configured in `backend/app.py`

---

## Phase 8: Integration Harness & CI

- [ ] T029 [P] Create `tests/integration/test_upload_query_reset.py` that runs: `/healthz` → upload sample → query → reset (measure timings)
- [ ] T030 [P] Add `.github/workflows/integration-rag.yml` CI job scaffold that runs integration harness when `CI_GEMINI_KEY` and `CI_CHROMA_CONFIG` secrets are present
- [ ] T031 Add `scripts/scan_committed_files_for_secrets.ps1` to enforce no hardcoded credentials in commits

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T032 [P] Add README quickstart at `specs/001-add-rag-kb/quickstart.md` with commands for local dev and CI
- [ ] T033 [P] Add documentation of dependency constraints in `specs/001-add-rag-kb/plan.md` and `backend/requirements.txt`
- [ ] T034 [P] Run formatting and linting on `backend/` using a minimal config (optional but recommended)

---

## Dependencies & Execution Order

- **Setup (Phase 1)** must complete before Foundational tasks begin.
- **Foundational (Phase 2)** tasks (T006-T012) block all user story implementation.
- **User Stories (Phase 3-5)** depend on Foundational completion; within each story, models/services must exist before endpoints.
- **Integration harness (Phase 8)** depends on User Stories 1-3 and Health tasks completion.

## Parallel Opportunities

- Tasks marked `[P]` are safe to run in parallel (different files, no direct dependency). Many foundational setup tasks (dependency pinning, env.example, scripts) can be done concurrently.
- Frontend UI tasks and backend API implementation for different endpoints can be implemented in parallel once foundational utilities (`chroma_client`, `embeddings`, `document_processor`) are available.

## Parallel Execution Example (per story)

- While `backend/chroma_client.py` is being implemented (T007), implement `backend/embeddings.py` (T008) and `backend/document_processor.py` (T009) in parallel.
- After foundational tasks complete, one engineer implements `POST /api/upload` (T013) while another implements the frontend upload UI (T015).

## Implementation Strategy

- MVP First: Implement minimal viable path: T001-T012 (setup + foundational) → T013 (upload) → T017 (query) → T024 (`/healthz`) → T029 (integration harness). Stop and run integration harness to validate the POC.
- Incremental Delivery: After MVP validation, implement reset (T021), polish UI, then CI job and gating.

## Files to Review / Update

- `backend/app.py` — main Flask app and endpoints
- `backend/embeddings.py` — Gemini wrapper
- `backend/chroma_client.py` — CloudClient helpers
- `backend/document_processor.py` — extract and chunk logic
- `tests/integration/test_upload_query_reset.py` — integration harness
- `frontend/index.html` and helper JS files — upload/query UI


**MVP Scope suggestion**: Complete User Story 1 (Upload) + User Story 2 (Query) + `/healthz` + integration harness `tests/integration/test_upload_query_reset.py`. This provides a runnable demo and satisfies constitution gates.

*** End of tasks.md
