"""
╔══════════════════════════════════════════════════════════════╗
║  Email Service — Email OSINT API Layer                       ║
║  Synchronous, serverless-safe (no threads, no global state)  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.email_lookup import EmailLookup
from utils.parser import categorise_result


def scan_email(email: str) -> dict:
    """
    Run the full email investigation pipeline:
      1. Gravatar check
      2. LeakCheck breach check
      3. HaveIBeenPwned (optional, needs API key)
      4. 30+ site registration checks

    Returns a clean JSON-serializable dict.
    """
    hibp_key = os.environ.get("HIBP_API_KEY", "")

    try:
        lookup = EmailLookup(hibp_api_key=hibp_key)
        all_results = lookup.scan(email)
    except Exception as e:
        return {
            "status": "error",
            "error": f"Email scan failed: {e}",
            "query": {"email": email},
        }

    # Categorize and clean
    for r in all_results:
        r["category"] = categorise_result(r)
        r.pop("profile_pic_data", None)  # strip binary for JSON

    linked = [r for r in all_results if r.get("exists")]
    breaches = [r for r in all_results if r.get("breach_data")]

    # Clean breach_data for JSON serialization
    breach_summaries = []
    for r in breaches:
        bd = r.get("breach_data", {})
        if bd:
            breach_summaries.append({
                "email": bd.get("email", email),
                "total_breaches": bd.get("total_breaches", 0),
                "total_sources": bd.get("total_sources", 0),
                "fields_exposed": bd.get("fields_exposed", []),
                "sources": bd.get("sources", []),
            })

    return {
        "status": "ok",
        "query": {"email": email},
        "summary": {
            "total_checked": len(all_results),
            "linked_accounts": len(linked),
            "breaches_found": len(breach_summaries),
        },
        "linked_accounts": linked,
        "breaches": breach_summaries,
        "all_results": all_results,
    }
