"""
╔══════════════════════════════════════════════════════════════╗
║  RECON OSINT — Flask Web Server                              ║
║  Serves the frontend + SSE-powered scan API                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import uuid
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, Response, stream_with_context

app = Flask(__name__,
            template_folder="templates",
            static_folder="static")
app.secret_key = os.urandom(24)

# Active scanners keyed by scan_id
_scanners: dict = {}


# ──────────────────────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main frontend page."""
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def start_scan():
    """Start a new scan. Returns a scan_id for SSE streaming."""
    data = request.get_json(force=True)

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    full_name = data.get("full_name", "").strip()
    deep = data.get("deep", False)

    if not username and not email and not full_name:
        return jsonify({"error": "No search query provided"}), 400

    # Load API keys from config
    api_key = ""
    cx_id = ""
    try:
        from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID
        api_key = GOOGLE_API_KEY or ""
        cx_id = SEARCH_ENGINE_ID or ""
    except ImportError:
        pass

    scan_id = str(uuid.uuid4())[:8]

    from web.scanner import WebScanner
    scanner = WebScanner()
    _scanners[scan_id] = scanner

    scanner.start_scan(
        username=username,
        email=email,
        full_name=full_name,
        deep=deep,
        api_key=api_key,
        cx_id=cx_id,
    )

    return jsonify({"scan_id": scan_id, "status": "started"})


@app.route("/api/scan/<scan_id>/stream")
def scan_stream(scan_id):
    """SSE endpoint — streams real-time scan events."""
    scanner = _scanners.get(scan_id)
    if not scanner:
        return jsonify({"error": "Scan not found"}), 404

    def generate():
        while True:
            try:
                event = scanner.queue.get(timeout=1.0)
                event_type = event["event"]
                event_data = event["data"]
                yield f"event: {event_type}\ndata: {event_data}\n\n"

                if event_type == "done":
                    # Cleanup
                    _scanners.pop(scan_id, None)
                    break
            except Exception:
                # Queue timeout — send heartbeat to keep connection alive
                if not scanner.is_running and scanner.queue.empty():
                    yield f"event: done\ndata: {{}}\n\n"
                    _scanners.pop(scan_id, None)
                    break
                yield f": heartbeat\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/scan/<scan_id>/stop", methods=["POST"])
def stop_scan(scan_id):
    """Stop a running scan."""
    scanner = _scanners.get(scan_id)
    if scanner:
        scanner.stop()
        return jsonify({"status": "stopping"})
    return jsonify({"error": "Scan not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
