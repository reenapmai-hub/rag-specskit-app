<!--
Sync Impact Report

- Version change: unknown -> 1.0.0
- Modified principles:
	- (new) Cloud-First Architecture
	- (new) External Embedding Provider (Zero Local Embeddings)
	- (new) Minimal Resource Footprint (Stateless Backend)
	- (new) API Key Security (env vars only)
	- (new) Fast Cold Starts (<2s target)
	- (new) Educational Transparency (visible retrieval details)
	- (new) Version Compatibility & Dependency Constraints
	- (new) Port & Runtime Defaults (backend default 5001)
	- (new) Integration Test Coverage (upload→query→reset)
- Added sections: Additional Constraints, Development Workflow (RAG-specific)
- Removed sections: none
- Templates requiring updates:
	- .specify/templates/plan-template.md ✅ updated
	- .specify/templates/spec-template.md ✅ updated
	- .specify/templates/tasks-template.md ✅ updated
- Follow-up TODOs:
	- RATIFICATION_DATE: TODO(RATIFICATION_DATE): original adoption date unknown; project lead to fill
-->

# RAG App Constitution

## Core Principles

### Cloud-First Architecture
All runtime vector storage and retrieval MUST use cloud-hosted ChromaDB Cloud (v2 API). Local or on-disk vector stores are PROHIBITED for production and CI tests that claim "cloud-first" compliance. Rationale: Simplifies deployment, scales independently, and aligns with cold-start goals.

### External Embedding Provider (Zero Local Embeddings)
All embeddings MUST be produced via a managed embeddings API (Gemini or equivalent). Generating or persisting embeddings locally or via downloaded models is PROHIBITED. Embedding operations MUST be stateless and invoked at ingestion/query time as needed.

### Minimal Resource Footprint (Stateless Backend)
Backends MUST not require local model artifacts or GPU resources. Services should be stateless where possible, use environment configuration for credentials, and keep memory/CPU usage minimal to meet fast cold starts.

### API Key Security
All secrets (ChromaDB API keys, Gemini credentials) MUST be supplied via environment variables and never committed. Developers MUST provide guidance for secure secret injection in CI/CD and deployment manifests.

### Fast Cold Starts
The system MUST be deployable and reach a query-ready state in under 2 seconds on supported cloud platforms (POC target). Design decisions that materially increase startup time are disallowed without explicit justification.

### Educational Transparency
Every query path MUST expose retrieval metadata (retrieved document ids, similarity scores, retrieval timestamps, and retrieval chain) to enable debugging and teachability. Defaults may redact sensitive content but must preserve scores/steps.

### Version Compatibility & Dependency Constraints
The project MUST target ChromaDB >=0.6.0 (v2 cloud API) and must constrain `numpy` to a <2.x range to maintain compatibility with ChromaDB. Any changes to minimum versions MUST follow governance rules for version bumps.

### Port & Runtime Defaults
Backend services MUST default to port `5001`. The constitution documents this as the standard to avoid macOS port conflicts and ensure consistent quickstart instructions.

### Integration Test Coverage (NON-NEGOTIABLE)
Integration tests MUST cover the upload→query→reset lifecycle using real credentials (in a gated CI environment or local developer-run step with ephemeral keys). Tests that mock the full cloud path can be supplementary but not replacements for the gated real-credentials test.

## Additional Constraints

- Dependency constraints: `chromadb >=0.6.0`, `numpy <2.0.0`.
- Embeddings: Managed API only (Gemini); no local embedding computation.
- Storage: ChromaDB Cloud only for vector storage used by the RAG pipeline.
- Observability: Retrieval traces and similarity scores MUST be logged and available via API responses or a debug endpoint.

## Development Workflow

- Secrets: Use environment variables and secrets managers. CI jobs that run the gated integration tests MUST obtain ephemeral credentials and revoke them after the run.
- Testing gates: Unit tests MAY run without cloud credentials. The final integration test for declaring feature "done" MUST run with real cloud credentials and pass upload→query→reset.
- Ports: Default backend port `5001`. Override via `PORT` env var only when necessary.

## Governance

- Amendments: Changes to principles that remove or redefine existing principles are MAJOR and require a written proposal, migration plan, and two approvers. Adding principles or clarifications is MINOR. Non-substantive wording/typo fixes are PATCH.
- Versioning policy: Follow semantic versioning for the constitution text: MAJOR for breaking governance changes, MINOR for adding principles, PATCH for clarifications.
- Compliance review: All PRs touching infra, deployment, or dependency versions MUST reference the constitution and include a short compliance checklist.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE) | **Last Amended**: 2026-02-13
