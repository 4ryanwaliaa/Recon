"""
╔══════════════════════════════════════════════════════════════╗
║  Search Service — Username + Google Dork API Layer           ║
║  Synchronous, serverless-safe (no threads, no global state)  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.username_checker import UsernameChecker, PLATFORMS
from modules.google_dork import GoogleDorkEngine
from modules.correlator import IdentityCorrelator
from utils.parser import categorise_result


def _get_api_keys():
    """Load API keys from config or environment."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    cx_id = os.environ.get("GOOGLE_CX_ID", "")
    if not api_key or not cx_id:
        try:
            from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID
            api_key = api_key or GOOGLE_API_KEY or ""
            cx_id = cx_id or SEARCH_ENGINE_ID or ""
        except ImportError:
            pass
    return api_key, cx_id


def search_username(username: str, deep: bool = False) -> dict:
    """
    Run a full username search:
      1. Google Dorking
      2. Username enumeration across 120+ platforms
      3. Identity correlation

    Returns a clean JSON-serializable dict.
    """
    api_key, cx_id = _get_api_keys()
    all_results = []

    # ── Phase 1: Google Dorking ───────────────────────────────
    try:
        dork = GoogleDorkEngine(api_key=api_key, cx_id=cx_id, delay=0.3)
        dork_results = dork.scan_username(username, deep=deep)
        for r in dork_results:
            r["category"] = categorise_result(r)
        all_results.extend(dork_results)
    except Exception as e:
        all_results.append({
            "source": "google_dork", "error": True,
            "title": f"Dork error: {e}", "url": "",
        })

    # ── Phase 2: Username Enumeration ─────────────────────────
    try:
        checker = UsernameChecker(
            max_workers=15 if deep else 10,
            delay=0.05,
        )
        found = checker.scan(username, deep=deep)
        for r in found:
            r["category"] = categorise_result(r)
        all_results.extend(found)
    except Exception as e:
        all_results.append({
            "source": "username_check", "error": True,
            "platform": "Error", "url": "",
            "title": f"Username check error: {e}",
        })

    # ── Phase 3: Identity Correlation ─────────────────────────
    clusters = []
    try:
        correlator = IdentityCorrelator()
        clusters = correlator.correlate(all_results, target_username=username)
        # Strip binary pic data for JSON serialization
        for c in clusters:
            c.pop("profile_pic_data", None)
    except Exception:
        pass

    # ── Build response ────────────────────────────────────────
    profiles = [r for r in all_results if r.get("category") == "profile" and r.get("exists")]
    documents = [r for r in all_results if r.get("category") == "document"]
    mentions = [r for r in all_results if r.get("category") == "mention"]

    # Strip binary data
    for r in all_results:
        r.pop("profile_pic_data", None)

    return {
        "status": "ok",
        "query": {"username": username, "deep": deep},
        "summary": {
            "total": len(all_results),
            "profiles": len(profiles),
            "documents": len(documents),
            "mentions": len(mentions),
            "clusters": len(clusters),
        },
        "results": {
            "profiles": profiles,
            "documents": documents,
            "mentions": mentions,
        },
        "identity_clusters": clusters,
    }


def search_fullname(full_name: str, deep: bool = False) -> dict:
    """
    Search by full name using Google Dorking.
    Returns a clean JSON-serializable dict.
    """
    api_key, cx_id = _get_api_keys()
    all_results = []

    try:
        dork = GoogleDorkEngine(api_key=api_key, cx_id=cx_id, delay=0.3)
        dork_results = dork.scan_username(full_name, deep=deep)
        for r in dork_results:
            r["category"] = categorise_result(r)
        all_results.extend(dork_results)
    except Exception as e:
        all_results.append({
            "source": "google_dork", "error": True,
            "title": f"Dork error: {e}", "url": "",
        })

    profiles = [r for r in all_results if r.get("category") == "profile"]
    documents = [r for r in all_results if r.get("category") == "document"]
    mentions = [r for r in all_results if r.get("category") == "mention"]

    for r in all_results:
        r.pop("profile_pic_data", None)

    return {
        "status": "ok",
        "query": {"full_name": full_name, "deep": deep},
        "summary": {
            "total": len(all_results),
            "profiles": len(profiles),
            "documents": len(documents),
            "mentions": len(mentions),
        },
        "results": {
            "profiles": profiles,
            "documents": documents,
            "mentions": mentions,
        },
    }
