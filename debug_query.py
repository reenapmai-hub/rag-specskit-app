#!/usr/bin/env python
import json
from backend import chroma_client
from backend.chroma_client import create_client, get_or_create_collection

client = create_client()
collection = chroma_client.get_or_create_collection(client)
res = chroma_client.query_similar(collection, 'RAG', top_k=3, min_score=0.25)
print('len=', len(res))
print(json.dumps(res, indent=2))
