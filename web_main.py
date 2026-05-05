"""
╔══════════════════════════════════════════════════════════════╗
║   RECON — OSINT Intelligence Scanner                         ║
║   Production-ready Flask backend                             ║
║                                                              ║
║   Compatible with:                                           ║
║     • Vercel  (@vercel/python serverless)                     ║
║     • Render  (gunicorn web_main:app)                         ║
║     • Local   (python web_main.py)                            ║
║                                                              ║
║   API Routes:                                                ║
║     GET  /              → serves frontend                    ║
║     POST /search        → username / fullname search         ║
║     POST /email-scan    → email investigation                ║
║     POST /image-scan    → reverse image search               ║
║     POST /api/scan      → SSE-powered scan (Render only)     ║
║     GET  /api/scan/<id>/stream → SSE stream (Render only)    ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys

# Ensure project root is on the path so imports work everywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, render_template

# ──────────────────────────────────────────────────────────────
#  App Init
# ──────────────────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
)
app.secret_key = os.environ.get("FLASK_SECRET", os.urandom(24))


# ──────────────────────────────────────────────────────────────
#  ROUTE: Frontend Pages
# ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the landing / home page."""
    from web.blog_data import get_all_articles
    latest = get_all_articles()[:3]
    return render_template("home.html", active_page="home", latest_articles=latest)


@app.route("/tool")
def tool():
    """Serve the OSINT scanner tool page."""
    return render_template("tool.html", active_page="tool")


@app.route("/blog")
def blog_list():
    """Serve the blog listing page."""
    from web.blog_data import get_all_articles
    return render_template("blog_list.html", active_page="blog", articles=get_all_articles())


@app.route("/blog/<slug>")
def blog_post(slug):
    """Serve a single blog article."""
    from web.blog_data import get_article_by_slug, get_related_articles
    article = get_article_by_slug(slug)
    if not article:
        return render_template("home.html", active_page="home", latest_articles=[]), 404
    related = get_related_articles(slug, limit=3)
    return render_template("blog_post.html", active_page="blog", article=article, related=related)


@app.route("/guides")
def guides():
    """Serve the cybersecurity guides page."""
    return render_template("guides.html", active_page="guides")


@app.route("/about")
def about():
    """Serve the about page."""
    return render_template("about.html", active_page="about")


@app.route("/contact")
def contact():
    """Serve the contact page."""
    return render_template("contact.html", active_page="contact")


@app.route("/privacy-policy")
def privacy_policy():
    """Serve the privacy policy page."""
    return render_template("privacy.html", active_page="privacy")


@app.route("/terms")
def terms():
    """Serve the terms and conditions page."""
    return render_template("terms.html", active_page="terms")


@app.route("/ads.txt")
def ads_txt():
    """Serve the AdSense ads.txt file."""
    return app.send_static_file("ads.txt")


# ══════════════════════════════════════════════════════════════
#  SERVERLESS-SAFE API ROUTES
#  These are stateless, synchronous, and work on Vercel + Render
# ══════════════════════════════════════════════════════════════

@app.route("/search", methods=["POST"])
def search():
    """
    Username or full-name search.

    Request JSON:
        { "username": "...", "deep": false }
        or
        { "full_name": "...", "deep": false }

    Returns JSON with results, summary, and identity clusters.
    """
    data = request.get_json(force=True, silent=True) or {}

    username = data.get("username", "").strip()
    full_name = data.get("full_name", "").strip()
    deep = data.get("deep", False)

    if not username and not full_name:
        return jsonify({"status": "error", "error": "Provide 'username' or 'full_name'"}), 400

    from services.search import search_username, search_fullname

    if username:
        result = search_username(username, deep=deep)
    else:
        result = search_fullname(full_name, deep=deep)

    return jsonify(result)


@app.route("/email-scan", methods=["POST"])
def email_scan():
    """
    Email investigation — breach checks + site registration detection.

    Request JSON:
        { "email": "user@example.com" }

    Returns JSON with linked accounts and breach data.
    """
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip()

    if not email:
        return jsonify({"status": "error", "error": "Provide 'email'"}), 400

    from services.email import scan_email
    result = scan_email(email)
    return jsonify(result)


@app.route("/image-scan", methods=["POST"])
def image_scan():
    """
    Reverse image search.

    Request JSON:
        { "image_url": "https://...", "deep": false }

    Returns JSON with image match results.
    """
    data = request.get_json(force=True, silent=True) or {}
    image_url = data.get("image_url", "").strip()
    deep = data.get("deep", False)

    if not image_url:
        return jsonify({"status": "error", "error": "Provide 'image_url'"}), 400

    from services.image import scan_image
    result = scan_image(image_url, deep=deep)
    return jsonify(result)


# ══════════════════════════════════════════════════════════════
#  SSE-POWERED SCAN API  (Render / local only — NOT for Vercel)
#  Preserved for the existing frontend that uses EventSource
# ══════════════════════════════════════════════════════════════

import uuid
import json

_scanners: dict = {}


@app.route("/api/scan", methods=["POST"], strict_slashes=False)
def start_scan():
    """Start a new SSE-powered scan. Returns scan_id for streaming."""
    data = request.get_json(force=True, silent=True) or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    full_name = data.get("full_name", "").strip()
    deep = data.get("deep", False)

    if not username and not email and not full_name:
        return jsonify({"error": "No search query provided"}), 400

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


@app.route("/api/scan/<scan_id>/stream", strict_slashes=False)
def scan_stream(scan_id):
    """SSE endpoint — streams real-time scan events."""
    from flask import Response, stream_with_context

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
                    _scanners.pop(scan_id, None)
                    break
            except Exception:
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


@app.route("/api/scan/<scan_id>/stop", methods=["POST"], strict_slashes=False)
def stop_scan(scan_id):
    """Stop a running scan."""
    scanner = _scanners.get(scan_id)
    if scanner:
        scanner.stop()
        return jsonify({"status": "stopping"})
    return jsonify({"error": "Scan not found"}), 404


# ══════════════════════════════════════════════════════════════
#  Health Check
# ══════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "RECON OSINT"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
