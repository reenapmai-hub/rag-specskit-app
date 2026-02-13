"""Direct test of frontend and backend together."""
import socket
import time

print("Checking port availability...")

def check_port(port, name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    if result == 0:
        print(f"✅ {name} listening on port {port}")
        return True
    else:
        print(f"❌ {name} NOT listening on port {port}")
        return False

frontend_ok = check_port(3000, "Frontend")
backend_ok = check_port(5001, "Backend")

if frontend_ok and backend_ok:
    print("\n✅ Both servers are running!")
    print("\n📋 Next Steps:")
    print("  1. Open http://localhost:3000 in your browser")
    print("  2. Upload a test file (test_upload.txt)")
    print("  3. Ask a question to search the uploaded document")
    print("  4. View results with similarity scores")
    print("  5. Click 'Reset Collection' to clear data")
else:
    print("\n⚠️  One or more servers are not responding")
    if not backend_ok:
        print("   Start backend: python backend/app.py")
    if not frontend_ok:
        print("   Start frontend: python serve_frontend.py")
