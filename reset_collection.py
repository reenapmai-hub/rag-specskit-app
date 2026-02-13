#!/usr/bin/env python
"""Reset the ChromaDB collection to accept 3072-dim embeddings"""

import os
from dotenv import load_dotenv
load_dotenv()

from backend.chroma_client import load_credentials, create_client, COLLECTION_NAME

try:
    print("Resetting ChromaDB collection...")
    
    creds = load_credentials()
    print(f"✓ Credentials loaded")
    
    client = create_client()
    print(f"✓ Client created")
    
    # Delete existing collection
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"✓ Deleted existing collection '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"⚠ Collection didn't exist or couldn't be deleted: {e}")
    
    # Recreate collection (will be created with new embeddings on first upsert)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    print(f"✓ Created new collection '{COLLECTION_NAME}'")
    print(f"✓ Collection is ready for 3072-dimensional embeddings")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import sys
    sys.exit(1)
