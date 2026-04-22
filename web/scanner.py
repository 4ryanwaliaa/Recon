"""
╔══════════════════════════════════════════════════════════════╗
║  Web Scanner — Bridges existing OSINT modules to SSE queue   ║
║  Runs scans in background threads, pushes events to a queue  ║
╚══════════════════════════════════════════════════════════════╝
"""

import queue
import json
import time
import threading
from typing import Optional


class WebScanner:
    """
    Wraps existing scan modules and pushes events to a queue
    that the SSE endpoint reads from.
    """

    def __init__(self):
        self.queue = queue.Queue()
        self._stop = False
        self._thread: Optional[threading.Thread] = None
        self._all_results = []
        self._p = self._d = self._m = 0

    def stop(self):
        self._stop = True
        for attr in ('_dork', '_ucheck', '_elookup'):
            eng = getattr(self, attr, None)
            if eng:
                eng.stop()

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _push(self, event_type: str, data: dict):
        """Push an SSE event to the queue."""
        self.queue.put({
            "event": event_type,
            "data": json.dumps(data, default=str),
        })

    def _cb(self, module, message, progress, results):
        """Callback adapter — same signature as the desktop ScanWorker._cb."""
        if self._stop:
            return

        from utils.parser import categorise_result

        self._push("log", {"level": "scan", "message": f"[{module}] {message}"})
        self._push("progress", {"module": module, "value": progress})

        for r in results:
            r["category"] = categorise_result(r)
            self._all_results.append(r)

            is_simulated = r.get("simulated", False)
            is_error = r.get("error", False)
            has_url = bool(r.get("url", ""))

            if has_url and not is_simulated and not is_error:
                self._push("result", r)

            if r["category"] == "profile":
                self._p += 1
            elif r["category"] == "document":
                self._d += 1
            else:
                self._m += 1

        self._push("stats", {
            "profiles": self._p,
            "documents": self._d,
            "mentions": self._m,
        })

    def start_scan(self, username="", email="", full_name="",
                   deep=False, api_key="", cx_id=""):
        """Launch the scan pipeline in a background thread."""
        self._stop = False
        self._all_results = []
        self._p = self._d = self._m = 0

        # Drain any leftover events
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

        def _run():
            try:
                # Phase 1: Google Dorking
                if not self._stop:
                    self._push("log", {"level": "info", "message": "━" * 50})
                    self._push("log", {"level": "info", "message": ">> PHASE 1: Google Dorking"})
                    self._push("log", {"level": "info", "message": "━" * 50})
                    from modules.google_dork import GoogleDorkEngine
                    self._dork = GoogleDorkEngine(
                        api_key=api_key, cx_id=cx_id, delay=0.3
                    )
                    if username and not self._stop:
                        self._dork.scan_username(username, callback=self._cb, deep=deep)
                    if email and not self._stop:
                        self._dork.scan_email(email, callback=self._cb, deep=deep)
                    if full_name and not self._stop:
                        self._dork.scan_username(full_name, callback=self._cb, deep=deep)

                # Phase 2: Username Enumeration
                if username and not self._stop:
                    self._push("log", {"level": "info", "message": "━" * 50})
                    self._push("log", {"level": "info", "message": ">> PHASE 2: Username Enumeration"})
                    self._push("log", {"level": "info", "message": "━" * 50})
                    from modules.username_checker import UsernameChecker
                    self._ucheck = UsernameChecker(
                        max_workers=15 if deep else 10, delay=0.05
                    )
                    self._ucheck.scan(username, callback=self._cb, deep=deep)

                # Phase 2.5: Profile Enrichment
                found_profiles = [
                    r for r in self._all_results
                    if r.get("exists") and r.get("source") == "username_check"
                ]
                if found_profiles and not self._stop:
                    self._push("log", {"level": "info", "message": "━" * 50})
                    self._push("log", {"level": "info", "message": ">> PHASE 2.5: Profile Enrichment"})
                    self._push("log", {"level": "info", "message": "━" * 50})
                    from modules.enrichment import ProfileEnricher
                    enricher = ProfileEnricher(delay=0.3)
                    total = len(found_profiles)
                    for i, r in enumerate(found_profiles):
                        if self._stop:
                            break
                        enricher.enrich(r, callback=self._cb)
                        self._push("enriched", r)
                        self._push("progress", {
                            "module": "Enrichment",
                            "value": int(((i + 1) / total) * 100),
                        })

                # Phase 3: Email Investigation
                if email and not self._stop:
                    self._push("log", {"level": "info", "message": "━" * 50})
                    self._push("log", {"level": "info", "message": ">> PHASE 3: Email Investigation"})
                    self._push("log", {"level": "info", "message": "━" * 50})
                    from modules.email_lookup import EmailLookup
                    self._elookup = EmailLookup()
                    self._elookup.scan(email, callback=self._cb)

                # Phase 4: Identity Correlation
                if not self._stop:
                    self._push("log", {"level": "info", "message": "━" * 50})
                    self._push("log", {"level": "info", "message": ">> PHASE 4: Identity Correlation"})
                    self._push("log", {"level": "info", "message": "━" * 50})
                    from modules.correlator import IdentityCorrelator
                    correlator = IdentityCorrelator()
                    clusters = correlator.correlate(
                        self._all_results, target_username=username or ""
                    )
                    self._push("log", {"level": "success",
                                       "message": f"Found {len(clusters)} identity cluster(s)"})
                    self._push("correlation", {"clusters": clusters})

                # Done
                if not self._stop:
                    self._push("log", {"level": "success", "message": "━" * 50})
                    self._push("log", {"level": "success", "message": "SCAN COMPLETE"})
                    self._push("log", {"level": "success",
                                       "message": f"Total: {len(self._all_results)} results "
                                                   f"({self._p} profiles, {self._d} docs, "
                                                   f"{self._m} mentions)"})
                    self._push("log", {"level": "success", "message": "━" * 50})
                else:
                    self._push("log", {"level": "warning", "message": "Scan stopped by user."})

            except Exception as e:
                self._push("log", {"level": "error", "message": f"Scan error: {e}"})

            self._push("done", {
                "total": len(self._all_results),
                "profiles": self._p,
                "documents": self._d,
                "mentions": self._m,
            })

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
