#!/usr/bin/env python
"""Quick route verification for Flask app."""

from backend.app import app

print("✅ Flask app imported successfully\n")

print("Registered routes:")
for rule in app.url_map.iter_rules():
    if rule.endpoint != "static":
        methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
        print(f"  {rule.rule:<25} {', '.join(methods)}")

print("\n✅ All routes registered")
