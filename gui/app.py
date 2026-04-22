"""
╔══════════════════════════════════════════════════════════════╗
║  RECON OSINT — Main Application Window                      ║
║  Scrollable layout + card-style results + crash fixes       ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTabWidget,
    QFileDialog, QApplication, QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QUrl
from PySide6.QtGui import QDesktopServices

from gui.components import (
    SearchHero, TerminalLog, ScanProgressPanel,
    CardScrollArea, GlowSeparator, PulsingDot, BreachCard, apply_glow,
)
from utils.parser import build_report, export_json


# ══════════════════════════════════════════════════════════════
#  Scan Worker Thread
# ══════════════════════════════════════════════════════════════

class ScanWorker(QObject):
    log = Signal(str, str)
    progress = Signal(str, int)
    result_found = Signal(dict)       # only REAL results (not simulated/errors)
    result_enriched = Signal(dict)    # enriched result (replaces card)
    correlation_done = Signal(list)   # identity clusters
    finished = Signal(list)
    stats_update = Signal(int, int, int)

    def __init__(self, username, email, full_name, mode, api_key="", cx_id="",
                 search_mode="Username"):
        super().__init__()
        self.username = username
        self.email = email
        self.full_name = full_name
        self.mode = mode
        self.api_key = api_key
        self.cx_id = cx_id
        self.search_mode = search_mode
        self._stop = False
        self._all = []
        self._p = self._d = self._m = 0

    def stop(self):
        self._stop = True
        for attr in ('_dork', '_ucheck', '_elookup', '_rimgsearch'):
            eng = getattr(self, attr, None)
            if eng:
                eng.stop()

    def _cb(self, module, message, progress, results):
        if self._stop:
            return
        self.log.emit("scan", f"[{module}] {message}")
        self.progress.emit(module, progress)

        from utils.parser import categorise_result
        for r in results:
            r["category"] = categorise_result(r)
            self._all.append(r)

            # Only emit to card UI if it's a REAL result (not simulated/error)
            is_simulated = r.get("simulated", False)
            is_error = r.get("error", False)
            has_url = bool(r.get("url", ""))

            if has_url and not is_simulated and not is_error:
                self.result_found.emit(r)

            if r["category"] == "profile":
                self._p += 1
            elif r["category"] == "document":
                self._d += 1
            else:
                self._m += 1

        self.stats_update.emit(self._p, self._d, self._m)

    def run(self):
        deep = self.mode == "deep"
        try:
            # ── Standard OSINT scan pipeline ──

            # Phase 1: Google Dorking
            if not self._stop:
                self.log.emit("info", "\u2501" * 50)
                self.log.emit("info", ">> PHASE 1: Google Dorking")
                self.log.emit("info", "\u2501" * 50)
                from modules.google_dork import GoogleDorkEngine
                self._dork = GoogleDorkEngine(
                    api_key=self.api_key, cx_id=self.cx_id, delay=0.3
                )
                if self.username and not self._stop:
                    self._dork.scan_username(self.username, callback=self._cb, deep=deep)
                if self.email and not self._stop:
                    self._dork.scan_email(self.email, callback=self._cb, deep=deep)
                if self.full_name and not self._stop:
                    self._dork.scan_username(self.full_name, callback=self._cb, deep=deep)

            # Phase 2: Username Enumeration
            if self.username and not self._stop:
                self.log.emit("info", "\u2501" * 50)
                self.log.emit("info", ">> PHASE 2: Username Enumeration")
                self.log.emit("info", "\u2501" * 50)
                from modules.username_checker import UsernameChecker
                self._ucheck = UsernameChecker(
                    max_workers=15 if deep else 10, delay=0.05
                )
                self._ucheck.scan(self.username, callback=self._cb, deep=deep)

            # Phase 2.5: Profile Enrichment
            found_profiles = [r for r in self._all if r.get("exists") and r.get("source") == "username_check"]
            if found_profiles and not self._stop:
                self.log.emit("info", "\u2501" * 50)
                self.log.emit("info", ">> PHASE 2.5: Profile Enrichment")
                self.log.emit("info", "\u2501" * 50)
                from modules.enrichment import ProfileEnricher
                self._enricher = ProfileEnricher(delay=0.3)
                total = len(found_profiles)
                for i, r in enumerate(found_profiles):
                    if self._stop:
                        break
                    self._enricher.enrich(r, callback=self._cb)
                    self.result_enriched.emit(r)
                    self.progress.emit("Enrichment", int(((i+1)/total)*100))

            # Phase 3: Email Investigation
            if self.email and not self._stop:
                self.log.emit("info", "\u2501" * 50)
                self.log.emit("info", ">> PHASE 3: Email Investigation")
                self.log.emit("info", "\u2501" * 50)
                from modules.email_lookup import EmailLookup
                self._elookup = EmailLookup()
                self._elookup.scan(self.email, callback=self._cb)

            # Phase 4: Identity Correlation
            if not self._stop:
                self.log.emit("info", "\u2501" * 50)
                self.log.emit("info", ">> PHASE 4: Identity Correlation")
                self.log.emit("info", "\u2501" * 50)
                from modules.correlator import IdentityCorrelator
                correlator = IdentityCorrelator()
                clusters = correlator.correlate(self._all, target_username=self.username or "")
                self.log.emit("success", f"Found {len(clusters)} identity cluster(s)")
                self.correlation_done.emit(clusters)

            # Done
            if not self._stop:
                self.log.emit("success", "\u2501" * 50)
                self.log.emit("success", "SCAN COMPLETE")
                self.log.emit("success",
                    f"Total: {len(self._all)} results "
                    f"({self._p} profiles, {self._d} docs, {self._m} mentions)")
                self.log.emit("success", "\u2501" * 50)
            else:
                self.log.emit("warning", "Scan stopped by user.")

        except Exception as e:
            self.log.emit("error", f"Scan error: {e}")

        self.finished.emit(self._all)


# ══════════════════════════════════════════════════════════════
#  Main Window
# ══════════════════════════════════════════════════════════════

class ReconApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RECON \u2014 OSINT Intelligence Scanner")
        self.setMinimumSize(1100, 750)
        self.resize(1400, 900)
        self._thread = None
        self._worker = None
        self._all_results = []
        self._load_styles()
        self._build_ui()
        self._load_api_config()
        self.statusBar().showMessage("Ready \u2014 Enter a target and start scanning")

    def _load_api_config(self):
        """Auto-fill API keys from config.py."""
        try:
            from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID
            if GOOGLE_API_KEY:
                self.hero.api_input.setText(GOOGLE_API_KEY)
            if SEARCH_ENGINE_ID:
                self.hero.cx_input.setText(SEARCH_ENGINE_ID)
        except ImportError:
            pass

    def _load_styles(self):
        p = Path(__file__).parent.parent / "assets" / "styles.qss"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    # ──────────────────────────────────────────────────────────
    #  UI Construction
    # ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Outer scroll area — makes the ENTIRE page scrollable ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #000000; border: none; }
            QScrollArea > QWidget > QWidget { background-color: #000000; }
        """)
        self.setCentralWidget(scroll)

        # ── Scrollable container ──
        container = QWidget()
        container.setStyleSheet("background-color: #000000;")
        main = QVBoxLayout(container)
        main.setContentsMargins(20, 0, 20, 10)
        main.setSpacing(10)

        # ── OPSIS-style Search Hero ──
        self.hero = SearchHero()
        self.hero.search_requested.connect(self._on_search_requested)
        main.addWidget(self.hero)

        # ── Stop button (hidden until scan starts) ──
        stop_row = QHBoxLayout()
        stop_row.setAlignment(Qt.AlignCenter)
        self.stop_btn = QPushButton("■  STOP SCAN")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setFixedWidth(200)
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.clicked.connect(self._stop_scan)
        self.stop_btn.setVisible(False)
        stop_row.addWidget(self.stop_btn)
        main.addLayout(stop_row)

        main.addWidget(GlowSeparator())

        # ── Progress section ──
        self.progress_panel = ScanProgressPanel()
        main.addWidget(self.progress_panel)

        # ── Terminal log (fixed height so it doesn't collapse) ──
        self.terminal = TerminalLog()
        self.terminal.setMinimumHeight(220)
        self.terminal.setMaximumHeight(300)
        main.addWidget(self.terminal)

        main.addWidget(GlowSeparator())

        # ── Results header + filter ──
        main.addWidget(self._build_results_header())


        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("\U0001f50d  Filter results...")
        self.filter_input.textChanged.connect(self._filter)
        self.filter_input.setStyleSheet("""
            QLineEdit { background:#080808; color:#ccc; border:1px solid #1a1a1a;
                        border-radius:4px; padding:8px 12px; font-size:12px; }
            QLineEdit:focus { border-color:#ff0033; }
        """)
        main.addWidget(self.filter_input)

        # ── Tabs with card scroll areas (fixed tall height) ──
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMinimumHeight(500)
        self.all_cards = CardScrollArea()
        self.profile_cards = CardScrollArea()
        self.doc_cards = CardScrollArea()
        self.mention_cards = CardScrollArea()
        self.identity_cards = CardScrollArea()
        self.tabs.addTab(self.all_cards,      "ALL RESULTS")
        self.tabs.addTab(self.profile_cards,  "PROFILES")
        self.tabs.addTab(self.doc_cards,      "DOCUMENTS")
        self.tabs.addTab(self.mention_cards,  "MENTIONS")
        self.tabs.addTab(self.identity_cards, "IDENTITIES")
        main.addWidget(self.tabs)

        # Spacer at bottom
        main.addStretch()

        scroll.setWidget(container)

    # ──────────────────────────────────────────────────────────
    #  Results Header Builder
    # ──────────────────────────────────────────────────────────

    def _build_results_header(self):
        """Build the results header row with title and action buttons."""
        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 8, 0, 4)
        row.setSpacing(10)

        title = QLabel("▎ RESULTS")
        title.setObjectName("sectionLabel")
        row.addWidget(title)
        row.addStretch()

        self.export_btn = QPushButton("⬇ EXPORT")
        self.export_btn.setObjectName("exportButton")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export)
        row.addWidget(self.export_btn)

        self.copy_btn = QPushButton("⎘ COPY URLs")
        self.copy_btn.setObjectName("copyButton")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_urls)
        row.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("✕ CLEAR")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear)
        row.addWidget(self.clear_btn)

        return header

    # ──────────────────────────────────────────────────────────
    #  Scan Control
    # ──────────────────────────────────────────────────────────

    def _on_search_requested(self, query, mode, deep):
        """Called when user clicks Search in the hero section."""
        import ast
        username = ""
        email = ""
        full_name = ""

        if mode == "Merge Scan":
            try:
                # Parse stringified dict safely
                query_dict = ast.literal_eval(query)
                username = query_dict.get("username", "")
                email = query_dict.get("email", "")
                full_name = query_dict.get("full_name", "")
            except:
                pass
        elif mode == "Username":
            username = query
        elif mode == "Email":
            email = query
        elif mode == "Full Name":
            full_name = query  # Use full name as search term

        self._start_scan(username, email, full_name, deep, mode)

    def _start_scan(self, username="", email="", full_name="", deep=False, search_mode="Username"):
        if not username and not email and not full_name:
            self.terminal.append_line("error", "Please enter a search query.")
            return

        # Reset UI
        self._all_results = []
        for area in (self.all_cards, self.profile_cards, self.doc_cards, self.mention_cards):
            area.clear_results()
        self.progress_panel.reset()
        self.terminal.clear_log()

        mode = "deep" if deep else "fast"
        api_key = self.hero.api_input.text().strip()
        cx_id = self.hero.cx_input.text().strip()

        # Log header
        self.terminal.append_line("info", "\u2550" * 55)
        self.terminal.append_line("found", "   RECON OSINT SCAN INITIATED")
        self.terminal.append_line("info", "\u2550" * 55)
        query_display_parts = []
        if username: query_display_parts.append(f"User: {username}")
        if email: query_display_parts.append(f"Email: {email}")
        if full_name: query_display_parts.append(f"Name: {full_name}")
        query_display = " | ".join(query_display_parts)
        
        self.terminal.append_line("info", "Search   : " + search_mode)
        self.terminal.append_line("info", "Query    : " + query_display)
        self.terminal.append_line("info", "Mode     : " + mode.upper())
        api_status = "Configured" if api_key else "Not set (dorking runs in simulation)"
        self.terminal.append_line("info", "Google API: " + api_status)
        self.terminal.append_line("info", "\u2550" * 55)

        # Toggle UI
        self.hero.search_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.hero.set_enabled_inputs(False)
        self.statusBar().showMessage("Scanning...")

        # Launch worker thread
        self._thread = QThread()
        self._worker = ScanWorker(
            username, email, full_name, mode, api_key, cx_id,
            search_mode=search_mode
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._on_log)
        self._worker.progress.connect(self.progress_panel.update_progress)
        self._worker.result_found.connect(self._on_result)
        self._worker.result_enriched.connect(self._on_enriched)
        self._worker.correlation_done.connect(self._on_correlation)
        self._worker.stats_update.connect(self.progress_panel.update_stats)
        self._worker.finished.connect(self._on_done)
        self._thread.start()

    def _stop_scan(self):
        if self._worker:
            self._worker.stop()
        self.terminal.append_line("warning", "Stop signal sent...")

    def _on_log(self, level, message):
        self.terminal.append_line(level, message)

    def _on_enriched(self, result):
        """Called when a profile is enriched — rebuild its card with DP/bio/followers."""
        has_new_data = bool(
            result.get("profile_pic_data")
            or result.get("bio")
            or result.get("followers")
        )
        if not has_new_data:
            return

        # Rebuild the card in ALL tabs that contain it
        self.all_cards.update_result(result)
        cat = result.get("category", "mention")
        if cat == "profile":
            self.profile_cards.update_result(result)
        elif cat == "document":
            self.doc_cards.update_result(result)
        else:
            self.mention_cards.update_result(result)

        platform = result.get("platform", "?")
        bio_preview = (result.get("bio", "") or "")[:40]
        followers = result.get("followers", 0)
        self.terminal.append_line(
            "found",
            f"Enriched {platform}: bio=\"{bio_preview}\" followers={followers}"
        )

    def _on_correlation(self, clusters):
        """Called when identity correlation is complete."""
        self.identity_cards.clear_results()
        for cluster in clusters:
            self.identity_cards.add_identity(cluster)
        n = len(clusters)
        self.tabs.setTabText(4, f"IDENTITIES ({n})")
        self.terminal.append_line("success", f"Correlation: {n} identities identified")

    def _on_result(self, result):
        """Only called for REAL results — filters low-quality entries."""
        self._all_results.append(result)

        # Check for breach data (LeakCheck) — render dedicated BreachCard
        breach_data = result.get("breach_data")
        if breach_data and result.get("platform") == "LeakCheck":
            try:
                self.all_cards.add_breach(breach_data)
                self.mention_cards.add_breach(breach_data)
            except Exception as e:
                self.terminal.append_line("error", f"Breach card error: {e}")
            return

        # Quality filter: skip results without valid URL or not found
        url = result.get("url", "")
        if not url or not url.startswith("http"):
            return
        if not result.get("exists", True):
            return

        # Add card to the appropriate tabs
        try:
            self.all_cards.add_result(result)
            cat = result.get("category", "mention")
            if cat == "profile":
                self.profile_cards.add_result(result)
            elif cat == "document":
                self.doc_cards.add_result(result)
            else:
                self.mention_cards.add_result(result)
        except Exception as e:
            self.terminal.append_line("error", f"Card render error: {e}")

    def _on_done(self, all_results):
        """Called when scan finishes (includes simulated results for export)."""
        # Re-enable UI
        self.hero.search_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.hero.set_enabled_inputs(True)

        # Store all results (including simulated) for export
        self._export_results = all_results

        n = len(self._all_results)
        self.export_btn.setEnabled(n > 0 or len(all_results) > 0)
        self.copy_btn.setEnabled(n > 0)
        self.statusBar().showMessage(f"Scan complete \u2014 {n} confirmed results found")

        # Clean up thread
        if self._thread:
            self._thread.quit()
            self._thread.wait(5000)

        # Update tab counts
        p = len([r for r in self._all_results if r.get("category") == "profile"])
        d = len([r for r in self._all_results if r.get("category") == "document"])
        m = len([r for r in self._all_results if r.get("category") == "mention"])
        self.tabs.setTabText(0, f"ALL ({n})")
        self.tabs.setTabText(1, f"PROFILES ({p})")
        self.tabs.setTabText(2, f"DOCUMENTS ({d})")
        self.tabs.setTabText(3, f"MENTIONS ({m})")

    # ──────────────────────────────────────────────────────────
    #  Actions
    # ──────────────────────────────────────────────────────────

    def _export(self):
        results = getattr(self, '_export_results', self._all_results)
        if not results:
            return
        query = self.hero.get_query()
        mode_name = self.hero.get_mode()
        deep = self.hero.deep_check.isChecked()
        scan_mode = "deep" if deep else "fast"
        name = f"recon_{query or 'scan'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", name, "JSON Files (*.json)")
        if path:
            report = build_report(query, "", results, scan_mode)
            export_json(report, path)
            self.terminal.append_line("success", f"Exported to: {path}")

    def _copy_urls(self):
        urls = self.all_cards.get_all_urls()
        if urls:
            QApplication.clipboard().setText("\n".join(urls))
            self.terminal.append_line("success", f"Copied {len(urls)} URLs to clipboard")

    def _clear(self):
        self._all_results = []
        self._export_results = []
        for area in (self.all_cards, self.profile_cards, self.doc_cards, self.mention_cards, self.identity_cards):
            area.clear_results()
        self.progress_panel.reset()
        self.terminal.clear_log()
        self.export_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.tabs.setTabText(0, "ALL RESULTS")
        self.tabs.setTabText(1, "PROFILES")
        self.tabs.setTabText(2, "DOCUMENTS")
        self.tabs.setTabText(3, "MENTIONS")
        self.tabs.setTabText(4, "IDENTITIES")

    def _filter(self, text):
        idx = self.tabs.currentIndex()
        areas = [self.all_cards, self.profile_cards, self.doc_cards, self.mention_cards]
        if 0 <= idx < len(areas):
            areas[idx].filter_cards(text)
