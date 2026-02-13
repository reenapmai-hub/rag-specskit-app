#!/usr/bin/env python3
"""Simple HTTP server for RAG frontend.

Run from repo root:
    python serve_frontend.py

Then visit http://localhost:3000/
"""
import http.server
import os
from pathlib import Path

PORT = 3000
FRONTEND_DIR = Path(__file__).parent / "frontend"

def run_server():
    # Change to frontend directory
    os.chdir(FRONTEND_DIR)
    
    # Create and run server
    Handler = http.server.SimpleHTTPRequestHandler
    server_address = ("127.0.0.1", PORT)
    
    with http.server.HTTPServer(server_address, Handler) as httpd:
        print(f"🚀 Serving frontend from {FRONTEND_DIR}")
        print(f"📂 Access at http://localhost:{PORT}")
        print(f"📂 API baseURL: http://localhost:5001/api")
        print(f"\n📄 Files being served:")
        for f in FRONTEND_DIR.glob("*"):
            if f.is_file():
                print(f"   - {f.name}")
        print("\n⏸️  Press CTRL+C to stop server\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Server stopped")

if __name__ == "__main__":
    run_server()
