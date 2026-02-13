#!/usr/bin/env python
"""Debug script to isolate the ChromaDB '_type' error"""

import os
import sys
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

import traceback

try:
    print("Step 1: Importing chromadb...")
    import chromadb
    print(f"✓ chromadb version: {chromadb.__version__}")

    print("\nStep 2: Loading credentials...")
    api_key = os.getenv("CHROMA_API_KEY", "").strip()
    tenant = os.getenv("CHROMA_TENANT", "").strip()
    database = os.getenv("CHROMA_DATABASE", "").strip()
    
    print(f"✓ API Key set: {bool(api_key)}")
    print(f"✓ Tenant: {tenant}")
    print(f"✓ Database: {database}")

    print("\nStep 3: Creating CloudClient...")
    client = chromadb.CloudClient(
        api_key=api_key,
        tenant=tenant,
        database=database,
    )
    print("✓ CloudClient created")

    print("\nStep 4: Creating collection (without metadata)...")
    collection = client.get_or_create_collection(
        name="rag-docs",
    )
    print(f"✓ Collection created, count: {collection.count()}")

    print("\nStep 5: Testing upsert with simple data...")
    collection.upsert(
        ids=["test-1"],
        documents=["This is a test document"],
        metadatas=[{"source": "test", "chunk_id": "0"}],
        embeddings=[[0.1] * 768],  # Mock 768-dim embedding
    )
    print(f"✓ Upsert successful, new count: {collection.count()}")

    print("\n✅ All tests passed!")

except Exception as e:
    print(f"\n❌ Error at step:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
