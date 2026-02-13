# Feature Specification: Cloud RAG Knowledge Base (upload + query + reset)

**Feature Branch**: `001-add-rag-kb`  
**Created**: 2026-02-13  
**Status**: Draft  
**Input**: User description: "Create a cloud-powered RAG knowledge system: drag-drop upload (.txt, .md, .pdf), local chunking, embeddings via Gemini text-embedding-004, vectors stored in ChromaDB Cloud (tenant: c15dd4dc-0b07-4ab4-a933-7d29a489dc7b), query embeddings via Gemini, return top-K chunks with similarity scores and metadata, remote reset wipes ChromaDB Cloud collection, real-time status (upload progress, embedding API calls, cloud sync confirmation). Constraints: chromadb >=0.6.0, numpy <2, backend default port 5001, secrets via env vars, no local model downloads, integration test: upload→query→reset with real credentials for final sign-off."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload & Index Documents (Priority: P1)

An end user drags and drops one or more documents (`.txt`, `.md`, `.pdf`) into the frontend. The browser performs client-side chunking, uploads chunks to the backend; the backend requests embeddings from the Gemini `text-embedding-004` model and stores vectors in ChromaDB Cloud (tenant `c15...9dc7b`). The UI displays upload progress, embedding API calls, and cloud sync confirmation. The user sees ingestion success and an ID for the uploaded collection.

**Why this priority**: Enables the core knowledge ingestion pipeline required for any retrieval; without it there is nothing to query.

**Independent Test**: Use the frontend to upload a 1KB `.txt` file and observe the UI progress indicators and the backend response.

**Acceptance Scenarios**:
1. **Given** an empty collection and valid env credentials, **When** the user uploads a 1KB `.txt` file, **Then** the upload completes in under 3 seconds (end-to-end: client chunking → Gemini embedding → ChromaDB cloud write) and the UI shows a successful cloud sync confirmation.
2. **Given** network or embedding errors, **When** a retry is attempted, **Then** the UI surfaces the error and a retry option; partial chunks should not produce inconsistent state in ChromaDB.

---

### User Story 2 - Natural Language Query & Retrieval (Priority: P1)

A user enters a natural language question in the frontend. The frontend sends the query to the backend; the backend obtains an embedding from Gemini, queries ChromaDB Cloud for top-K similar chunks, and returns the chunk texts with similarity scores and source metadata. The UI displays the retrieved snippets, scores, and a retrieval trace.

**Why this priority**: Core user-facing functionality that demonstrates retrieval quality, latency, and transparency.

**Independent Test**: Call the query endpoint with a sample question against the ingested collection and verify returned items and scores.

**Acceptance Scenarios**:
1. **Given** an indexed collection, **When** the user queries, **Then** the backend returns top-K results with similarity scores and source metadata within 2 seconds.
2. **Given** no relevant documents, **When** the user queries, **Then** the system returns an empty result set with a clear "no results" response and logs retrieval steps.

---

### User Story 3 - Remote Reset of Collection (Priority: P2)

An admin or developer triggers the reset endpoint which wipes the ChromaDB Cloud collection for the tenant. The reset does not delete local files on the user's machine; it only clears the cloud vector collection.

**Why this priority**: Enables test isolation and lifecycle management for gated integration tests and supports user-initiated cleanups.

**Independent Test**: Call the reset endpoint, then run a query and verify no results are returned.

**Acceptance Scenarios**:
1. **Given** a populated collection, **When** the reset endpoint is called, **Then** subsequent queries return no results and health reports the collection as empty.

---

### System Scenario - Health & Integration Gate (Priority: P1)

Provide a `/health` endpoint that verifies environment variables, Gemini embedding access (test call or token validity), and ChromaDB Cloud connectivity. This endpoint is used by CI to gate the final integration test.

**Independent Test**: Call `/health` and expect all checks to be "green".

---

### Edge Cases

- Large file uploads (10s of MB) — UI should stream progress and backend should enforce chunk size/limits.
- PDFs containing images or scanned pages — OCR is out of scope for MVP; such pages can be skipped or produce a metadata warning.
- Embedding API rate limits — system must surface rate-limit errors and provide retry/backoff.
- Partial failures during cloud writes — ensure idempotency keys for chunk writes to avoid duplicates.
- Tenant mismatch or invalid tenant id — health check should catch incorrect tenant configuration early.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]  
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

<!-- RAG-specific mandatory requirements (aligned with constitution) -->
- **FR-RAG-001**: System MUST use ChromaDB Cloud (v2 API) for vector storage in any deployment claiming "cloud-first" compliance.
- **FR-RAG-002**: Embeddings MUST be created via a managed embeddings API (e.g., Gemini); the system MUST NOT require local embedding computation.
- **FR-RAG-003**: Integration tests MUST include an upload→query→reset lifecycle executed with ephemeral or real credentials before feature sign-off.
- **FR-RAG-004**: Dependency constraints MUST be documented: `chromadb >=0.6.0`, `numpy <2.0.0`.

### Functional Requirements (concrete)

- **FR-010 (Upload)**: The system MUST accept drag-drop uploads of `.txt`, `.md`, and `.pdf` files via the frontend and perform client-side chunking before sending chunks to the backend.
- **FR-011 (Embedding)**: The backend MUST call Gemini `text-embedding-004` for all embedding requests (both ingestion and query) and must never perform local embedding computation.
- **FR-012 (Vector Storage)**: The backend MUST write vectors and metadata to ChromaDB Cloud under tenant `c15dd4dc-0b07-4ab4-a933-7d29a489dc7b` and expose a collection identifier to the UI.
- **FR-013 (Retrieval API)**: The backend MUST provide a query endpoint that accepts a natural language question and returns top-K chunks including text snippet, similarity score, source metadata, and retrieval trace.
- **FR-014 (Reset API)**: The backend MUST provide a reset endpoint that wipes the ChromaDB Cloud collection associated with the feature's collection identifier.
- **FR-015 (Health API)**: The backend MUST expose a `/health` endpoint validating: required env vars present, Gemini credential validity (smoke call or token check), and ChromaDB connectivity.
- **FR-016 (Observability)**: For each query, the system MUST return retrieval metadata (document id, chunk id, similarity score, retrieval timestamp) and log embedding and cloud write events.
- **FR-017 (Security)**: No credentials (Gemini keys, ChromaDB API keys, tenant ids) may be hard-coded or committed to source; they MUST be supplied via environment variables or secrets manager in CI/CD.
- **FR-018 (Port Default)**: Backend MUST default to port `5001` and support override via `PORT` environment variable.
- **FR-019 (Performance)**: Upload (1KB sample) end-to-end ingestion MUST complete in under 3 seconds; Query (single question) MUST return results within 2 seconds for typical small collections (POC target).

*Notes*: FR-019 performance targets are POC goals; CI tests must measure and record timings.

### Key Entities

- **Document**: Represents an uploaded source file. Attributes: `document_id`, `filename`, `mime_type`, `upload_timestamp`, `source_uri`.
- **Chunk**: A contiguous text slice of a `Document`. Attributes: `chunk_id`, `document_id`, `text`, `start_offset`, `end_offset`, `metadata`.
- **EmbeddingRecord**: Vector record stored in ChromaDB. Attributes: `record_id`, `chunk_id`, `vector`, `created_at`.
- **Collection**: Logical grouping in ChromaDB for this project's tenant. Attributes: `collection_id`, `tenant_id`, `created_at`, `item_count`.
- **QuerySession**: In-flight query context. Attributes: `session_id`, `query_text`, `query_embedding_meta`, `retrieved_items`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Health)**: `/health` returns all green checks (env vars, Gemini credential check, ChromaDB connectivity) — required for CI gate.
- **SC-002 (Upload Performance)**: Uploading a 1KB `.txt` file completes end-to-end (client chunk → Gemini embed → ChromaDB write) in under 3 seconds in the POC environment.
- **SC-003 (Query Performance)**: A query against a small collection returns top-K results with similarity scores in under 2 seconds.
- **SC-004 (Reset Effectiveness)**: After calling the reset endpoint, subsequent queries return no results and `/health` reflects an empty collection state.
- **SC-005 (Frontend Integration)**: The frontend successfully calls backend endpoints used in the UI (upload, query, reset, health) without 501/404 errors in standard quickstart.
- **SC-006 (Secrets Safety)**: No hardcoded credentials exist in the repository; scanning the tree for common secrets returns none in committed files.

## Assumptions

- Gemini embedding model used: `text-embedding-004` and the embedding API is accessible via provided credentials.
- ChromaDB Cloud tenant id to use: `c15dd4dc-0b07-4ab4-a933-7d29a489dc7b` (provided by user).
- Client-side chunking will be sufficient for POC; chunk size default: 500 tokens (approx 3–4KB) with 20% overlap unless overridden.
- Authentication: POC will allow unauthenticated uploads/queries behind ephemeral keys for CI; production authentication is out-of-scope for this MVP. [NEEDS CLARIFICATION: Should upload/query endpoints require authentication for MVP, or is unauthenticated POC acceptable?]

## Integration Test Plan

1. Provision ephemeral Gemini and ChromaDB credentials in CI secrets.
2. Run `/health` to validate environment and connectivity.
3. Upload a 1KB `.txt` via the frontend or API client; assert ingestion finishes <3s.
4. Run a natural language query; assert results with scores returned <2s.
5. Call the reset endpoint; run the same query and assert empty results.

## Notes & Next Steps

- Add a small integration test harness script under `tests/integration/test_upload_query_reset.py` that performs steps in the Integration Test Plan and records timings.
- Add CI job `integration-rag` that runs the harness only when ephemeral credentials are present (protected branch or manual run).

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]
