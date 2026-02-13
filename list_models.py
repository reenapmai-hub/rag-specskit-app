#!/usr/bin/env python
"""List available Gemini models"""

import os
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# List all available models
models = genai.list_models()
print("Available models:")
for model in models:
    print(f"  - {model.name}")
    if hasattr(model, 'supported_generation_methods'):
        print(f"    Methods: {model.supported_generation_methods}")
