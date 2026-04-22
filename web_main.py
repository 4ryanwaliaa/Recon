"""
╔══════════════════════════════════════════════════════════════╗
║   RECON — OSINT Intelligence Scanner (Web Version)           ║
║   Entry Point                                                ║
║                                                              ║
║   Usage:  python web_main.py                                 ║
║   Open:   http://localhost:5000                               ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import os

# Ensure project root is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.server import app

if __name__ == "__main__":
    print("=" * 55)
    print("   RECON OSINT -- Web Interface")
    print("=" * 55)
    print(f"   Open in browser: http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
