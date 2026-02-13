This project must:

- Use cloud-first architecture (ChromaDB Cloud, no local vector storage)
- Use Gemini API for all embeddings (no local embedding models)
- Avoid persistent local state (stateless backend)
- Store API keys only in environment variables
- Support fast cold starts (<2s from deploy to query-ready)
- Expose retrieval steps with similarity scores for learning purposes
- Enforce version constraints:
  - ChromaDB >= 0.6.0 (v2 API required for cloud)
  - numpy < 2
- Default backend port must be 5001
- Require integration test coverage for upload → query → reset before completion
