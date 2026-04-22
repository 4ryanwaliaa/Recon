"""
╔══════════════════════════════════════════════════════════════╗
║  GUI Components — OPSIS-Style OSINT Interface               ║
╚══════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QFrame, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect, QApplication, QLineEdit, QCheckBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QUrl, QByteArray
from PySide6.QtGui import (
    QColor, QPainter, QBrush, QPainterPath, QPixmap,
    QTextCursor, QDesktopServices, QPen, QFont,
)


def apply_glow(widget, color="#ff0033", radius=15):
    effect = QGraphicsDropShadowEffect()
    effect.setColor(QColor(color))
    effect.setBlurRadius(radius)
    effect.setOffset(0, 0)
    widget.setGraphicsEffect(effect)


# ══════════════════════════════════════════════════════════════
#  OPSIS-Style Search Hero
# ══════════════════════════════════════════════════════════════

class SearchHero(QWidget):
    """Centered hero section: Logo + mode tabs + search bar + deep search."""

    search_requested = Signal(str, str, bool)  # (query, mode, deep)

    MODES = [
        ("Username", "Enter username..."),
        ("Email", "Enter email address..."),
        ("Full Name", "Enter full name..."),
        ("Merge Scan", "Multi-target scan..."),
    ]
    BADGES = {
        "Full Name": "BETA",
        "Merge Scan": "PRO",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_mode = 0
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 30, 0, 20)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        # ── Logo Icon ──
        logo = QLabel()
        logo.setFixedSize(60, 60)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 #ff0033, stop:1 #cc0029);
            border-radius: 14px;
            color: #000;
            font-size: 28px; font-weight: bold;
        """)
        logo.setText("⬡")
        apply_glow(logo, "#ff0033", 25)
        logo_container = QHBoxLayout()
        logo_container.setAlignment(Qt.AlignCenter)
        logo_container.addWidget(logo)

        # Title next to logo
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title_lbl = QLabel("RECON")
        title_lbl.setStyleSheet(
            "color:#ffffff; font-size:32px; font-weight:bold; "
            "letter-spacing:4px; background:transparent;"
        )
        sub_lbl = QLabel("O S I N T")
        sub_lbl.setStyleSheet(
            "color:#ff0033; font-size:11px; font-weight:bold; "
            "letter-spacing:6px; background:transparent; margin-top:-2px;"
        )
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)
        logo_container.addLayout(title_col)
        layout.addLayout(logo_container)

        layout.addSpacing(24)

        # ── Mode Tabs ──
        tabs_row = QHBoxLayout()
        tabs_row.setAlignment(Qt.AlignCenter)
        tabs_row.setSpacing(8)
        self._mode_btns = []
        for i, (name, _) in enumerate(self.MODES):
            btn = QPushButton(name)
            btn.setObjectName("modeTab")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setMinimumHeight(38)
            btn.setMinimumWidth(145 if len(name) > 8 else 125)

            # Add badge if applicable
            badge = self.BADGES.get(name, "")
            if badge:
                btn.setText(f"{name}  ")
                badge_lbl = QLabel(badge, btn)
                badge_lbl.setStyleSheet(
                    "background:#ff003344; color:#ff0033; font-size:8px; "
                    "font-weight:bold; border-radius:3px; padding:1px 4px; "
                    "border: 1px solid #ff003355;"
                )
                badge_lbl.setFixedHeight(14)
                badge_lbl.move(btn.minimumWidth() - 42, 4)

            btn.clicked.connect(lambda checked, idx=i: self._set_mode(idx))
            tabs_row.addWidget(btn)
            self._mode_btns.append(btn)
        self._update_tab_styles()
        layout.addLayout(tabs_row)

        layout.addSpacing(20)

        # ── Search Bar Container ──
        search_container = QHBoxLayout()
        search_container.setAlignment(Qt.AlignCenter)

        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_frame.setFixedWidth(740)
        search_frame.setFixedHeight(56)
        search_frame.setStyleSheet("""
            QFrame#searchFrame {
                background: #0a0a12;
                border: 1px solid #1a1a2e;
                border-radius: 12px;
            }
            QFrame#searchFrame:hover {
                border-color: #ff003366;
            }
        """)
        apply_glow(search_frame, "#ff0033", 10)

        bar_layout = QHBoxLayout(search_frame)
        bar_layout.setContentsMargins(18, 0, 6, 0)
        bar_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("heroSearchInput")
        self.search_input.setPlaceholderText(self.MODES[0][1])
        self.search_input.setStyleSheet("""
            QLineEdit#heroSearchInput {
                background: transparent; border: none;
                color: #ffffff; font-size: 15px;
                padding: 0; margin: 0;
            }
            QLineEdit#heroSearchInput::placeholder { color: #444455; }
        """)
        self.search_input.returnPressed.connect(self._do_search)
        bar_layout.addWidget(self.search_input, 1)

        # Merge scan container (hidden by default)
        self.merge_container = QWidget()
        self.merge_container.setVisible(False)
        merge_layout = QHBoxLayout(self.merge_container)
        merge_layout.setContentsMargins(0, 0, 0, 0)
        merge_layout.setSpacing(10)

        self.merge_user = QLineEdit()
        self.merge_user.setPlaceholderText("Username")
        self.merge_email = QLineEdit()
        self.merge_email.setPlaceholderText("Email")
        self.merge_name = QLineEdit()
        self.merge_name.setPlaceholderText("Full Name")

        for inp in (self.merge_user, self.merge_email, self.merge_name):
            inp.setStyleSheet("""
                QLineEdit {
                    background: transparent; border: none;
                    border-right: 1px solid #1a1a2e;
                    color: #ffffff; font-size: 13px;
                }
                QLineEdit::placeholder { color: #444455; }
            """)
            inp.returnPressed.connect(self._do_search)
            merge_layout.addWidget(inp, 1)
        # Remove right border from last input
        self.merge_name.setStyleSheet(self.merge_name.styleSheet().replace("border-right: 1px solid #1a1a2e;", ""))

        bar_layout.addWidget(self.merge_container, 1)

        # Browse button (hidden by default, shown for Reverse Image)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setObjectName("browseButton")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedSize(90, 38)
        self.browse_btn.setVisible(False)
        self.browse_btn.setStyleSheet("""
            QPushButton#browseButton {
                background: #1a1a2e; color: #888;
                border: 1px solid #2a2a3e; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton#browseButton:hover {
                background: #2a2a3e; color: #ff0033;
                border-color: #ff003366;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_image)
        bar_layout.addWidget(self.browse_btn)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("heroSearchButton")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setFixedSize(120, 42)
        self.search_btn.setStyleSheet("""
            QPushButton#heroSearchButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #cc0029, stop:1 #ff0033);
                color: #000; border: none; border-radius: 8px;
                font-size: 14px; font-weight: bold; letter-spacing: 1px;
            }
            QPushButton#heroSearchButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #ff0033, stop:1 #ff1a4d);
            }
            QPushButton#heroSearchButton:pressed {
                background: #990022;
            }
        """)
        self.search_btn.clicked.connect(self._do_search)
        bar_layout.addWidget(self.search_btn)

        search_container.addWidget(search_frame)
        layout.addLayout(search_container)

        layout.addSpacing(14)

        # ── Deep Search + Sources ──
        bottom_row = QHBoxLayout()
        bottom_row.setAlignment(Qt.AlignCenter)
        bottom_row.setSpacing(16)

        self.deep_check = QCheckBox("Deep Search")
        self.deep_check.setStyleSheet("""
            QCheckBox {
                color: #888; font-size: 12px; font-weight: bold;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid #333; border-radius: 3px;
                background: #0a0a12;
            }
            QCheckBox::indicator:checked {
                background: #ff0033; border-color: #ff0033;
            }
        """)
        bottom_row.addWidget(self.deep_check)

        sep = QLabel("|")
        sep.setStyleSheet("color:#333; font-size:14px; background:transparent;")
        bottom_row.addWidget(sep)

        dot = PulsingDot()
        dot._active = True
        dot._t.start()
        bottom_row.addWidget(dot)

        sources_lbl = QLabel("150+ Sources")
        sources_lbl.setStyleSheet(
            "color:#00cc66; font-size:12px; font-weight:bold; background:transparent;"
        )
        bottom_row.addWidget(sources_lbl)

        layout.addLayout(bottom_row)

        # ── API Config (collapsible) ──
        layout.addSpacing(10)
        self.api_toggle = QPushButton("▸ API Configuration")
        self.api_toggle.setObjectName("apiToggle")
        self.api_toggle.setCursor(Qt.PointingHandCursor)
        self.api_toggle.setStyleSheet("""
            QPushButton#apiToggle {
                background: transparent; border: none;
                color: #333; font-size: 11px; font-weight: bold;
                letter-spacing: 1px; padding: 4px;
            }
            QPushButton#apiToggle:hover { color: #ff0033; }
        """)
        self.api_toggle.clicked.connect(self._toggle_api)
        api_toggle_row = QHBoxLayout()
        api_toggle_row.setAlignment(Qt.AlignCenter)
        api_toggle_row.addWidget(self.api_toggle)
        layout.addLayout(api_toggle_row)

        self.api_panel = QWidget()
        self.api_panel.setVisible(False)
        api_layout = QHBoxLayout(self.api_panel)
        api_layout.setContentsMargins(80, 4, 80, 4)
        api_layout.setSpacing(10)

        api_lbl = QLabel("API KEY")
        api_lbl.setStyleSheet("color:#444; font-size:10px; font-weight:bold;")
        api_layout.addWidget(api_lbl)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Google Custom Search API key")
        self.api_input.setEchoMode(QLineEdit.Password)
        self.api_input.setMinimumHeight(32)
        self.api_input.setStyleSheet("""
            QLineEdit { background:#0a0a12; color:#888; border:1px solid #1a1a2e;
                        border-radius:6px; padding:6px 12px; font-size:11px; }
            QLineEdit:focus { border-color:#ff003366; }
        """)
        api_layout.addWidget(self.api_input, 1)

        cx_lbl = QLabel("CX ID")
        cx_lbl.setStyleSheet("color:#444; font-size:10px; font-weight:bold;")
        api_layout.addWidget(cx_lbl)

        self.cx_input = QLineEdit()
        self.cx_input.setPlaceholderText("Search Engine ID")
        self.cx_input.setMinimumHeight(32)
        self.cx_input.setStyleSheet("""
            QLineEdit { background:#0a0a12; color:#888; border:1px solid #1a1a2e;
                        border-radius:6px; padding:6px 12px; font-size:11px; }
            QLineEdit:focus { border-color:#ff003366; }
        """)
        api_layout.addWidget(self.cx_input, 1)

        layout.addWidget(self.api_panel)

    def _set_mode(self, idx):
        self._active_mode = idx
        for i, btn in enumerate(self._mode_btns):
            btn.setChecked(i == idx)
        self._update_tab_styles()
        
        is_merge = (idx == 3)
        self.search_input.setVisible(not is_merge)
        self.merge_container.setVisible(is_merge)
        if not is_merge:
            self.search_input.setPlaceholderText(self.MODES[idx][1])
            self.search_input.clear()
        else:
            self.merge_user.clear()
            self.merge_email.clear()
            self.merge_name.clear()
        # Show/hide browse button for Reverse Image mode
        self.browse_btn.setVisible(False)

    def _update_tab_styles(self):
        for i, btn in enumerate(self._mode_btns):
            if i == self._active_mode:
                btn.setStyleSheet("""
                    QPushButton#modeTab {
                        background: #ff0033; color: #000;
                        border: none; border-radius: 8px;
                        font-size: 13px; font-weight: bold;
                        padding: 8px 20px; letter-spacing: 0.5px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton#modeTab {
                        background: #0d0d18; color: #888;
                        border: 1px solid #1a1a2e; border-radius: 8px;
                        font-size: 13px; font-weight: bold;
                        padding: 8px 20px; letter-spacing: 0.5px;
                    }
                    QPushButton#modeTab:hover {
                        background: #151525; color: #ccc;
                        border-color: #ff003344;
                    }
                """)

    def _toggle_api(self):
        vis = not self.api_panel.isVisible()
        self.api_panel.setVisible(vis)
        self.api_toggle.setText("▾ API Configuration" if vis else "▸ API Configuration")

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif *.bmp)"
        )
        if path:
            self.search_input.setText(path)

    def _do_search(self):
        mode = self.MODES[self._active_mode][0]
        deep = self.deep_check.isChecked()
        
        if mode == "Merge Scan":
            query_dict = {
                "username": self.merge_user.text().strip(),
                "email": self.merge_email.text().strip(),
                "full_name": self.merge_name.text().strip()
            }
            if not any(query_dict.values()):
                return
            # Pass dict instead of string
            self.search_requested.emit(str(query_dict), mode, deep)
        else:
            query = self.search_input.text().strip()
            if not query:
                return
            self.search_requested.emit(query, mode, deep)

    def get_mode(self) -> str:
        return self.MODES[self._active_mode][0]

    def get_query(self) -> str:
        return self.search_input.text().strip()

    def set_enabled_inputs(self, enabled: bool):
        self.search_input.setEnabled(enabled)
        self.search_btn.setEnabled(enabled)
        for btn in self._mode_btns:
            btn.setEnabled(enabled)
        self.deep_check.setEnabled(enabled)
        self.api_input.setEnabled(enabled)
        self.cx_input.setEnabled(enabled)


# ══════════════════════════════════════════════════════════════
#  Terminal Log
# ══════════════════════════════════════════════════════════════

class TerminalLog(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(160)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #030303; color: #00ff41;
                border: 1px solid #111; border-radius: 6px; padding: 10px;
                font-family: "Cascadia Code","Fira Code","Consolas",monospace;
                font-size: 12px;
            }
        """)
        self.append_line("system", "RECON OSINT Scanner initialized.")

    def append_line(self, level, message):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {"system": "#666", "info": "#00ff41", "scan": "#3399ff",
                  "found": "#ff0033", "warning": "#ffaa00", "error": "#ff4444", "success": "#00cc66"}
        c = colors.get(level, "#888")
        self.append(
            f'<span style="color:#333">[{ts}]</span> '
            f'<span style="color:{c};font-weight:bold">[{level.upper()}]</span> '
            f'<span style="color:#ccc">{message}</span>'
        )
        cur = self.textCursor()
        cur.movePosition(QTextCursor.End)
        self.setTextCursor(cur)

    def clear_log(self):
        self.clear()
        self.append_line("system", "Log cleared.")


# ══════════════════════════════════════════════════════════════
#  Scan Progress Panel
# ══════════════════════════════════════════════════════════════

class ScanProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.overall_bar = QProgressBar()
        self.overall_bar.setRange(0, 100)
        self.overall_bar.setValue(0)
        self.overall_bar.setFormat("OVERALL \u2014 %p%")
        self.overall_bar.setMinimumHeight(22)
        apply_glow(self.overall_bar, "#ff0033", 8)
        layout.addWidget(self.overall_bar)
        self.module_bars = {}
        for mod in ["Google Dorking", "Username Check", "Enrichment", "Email Lookup"]:
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFormat(f"{mod} \u2014 %p%")
            bar.setMinimumHeight(16)
            bar.setStyleSheet("""
                QProgressBar { background:#0d0d0d; border:1px solid #111; border-radius:4px;
                               height:16px; text-align:center; font-size:10px; color:#666; }
                QProgressBar::chunk { background:#ff003388; border-radius:3px; }
            """)
            layout.addWidget(bar)
            self.module_bars[mod] = bar
        self.stats_label = QLabel("Found: 0 profiles | 0 documents | 0 mentions")
        self.stats_label.setObjectName("statsLabel")
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)

    def update_progress(self, module, value):
        if module in self.module_bars:
            self.module_bars[module].setValue(value)
        vals = [b.value() for b in self.module_bars.values()]
        self.overall_bar.setValue(int(sum(vals) / len(vals)) if vals else 0)

    def update_stats(self, p, d, m):
        self.stats_label.setText(f"Found: {p} profiles | {d} documents | {m} mentions")

    def reset(self):
        self.overall_bar.setValue(0)
        for b in self.module_bars.values():
            b.setValue(0)
        self.stats_label.setText("Found: 0 profiles | 0 documents | 0 mentions")


# ══════════════════════════════════════════════════════════════
#  Helper: Circular Pixmap
# ══════════════════════════════════════════════════════════════

def make_circular_pixmap(pixmap: QPixmap, size: int = 64) -> QPixmap:
    """Crop a pixmap into a circle."""
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)
    painter.end()
    return result


# ══════════════════════════════════════════════════════════════
#  Breach Intelligence Card (LeakCheck)
# ══════════════════════════════════════════════════════════════

class BreachCard(QFrame):
    """Premium card displaying breach intelligence data from LeakCheck."""

    def __init__(self, breach_data: dict, parent=None):
        super().__init__(parent)
        self.breach_data = breach_data
        self.setMinimumSize(380, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        total = breach_data.get("total_breaches", 0)
        # Color coding based on severity
        if total >= 100:
            self.accent = "#ff0033"   # critical red
        elif total >= 10:
            self.accent = "#ffaa00"   # warning orange
        elif total > 0:
            self.accent = "#ff6633"   # moderate
        else:
            self.accent = "#00cc66"   # clean green

        self.setStyleSheet(f"""
            BreachCard {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0c0c18, stop:1 #08080f);
                border: 1px solid {self.accent}44;
                border-top: 3px solid {self.accent};
                border-radius: 10px;
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)

        # ── Header row ──
        header = QHBoxLayout()
        header.setSpacing(10)

        icon_lbl = QLabel("🛡")
        icon_lbl.setStyleSheet(f"font-size:24px; background:transparent;")
        icon_lbl.setFixedWidth(32)
        header.addWidget(icon_lbl)

        title = QLabel("BREACH INTELLIGENCE")
        title.setStyleSheet(f"""
            color: {self.accent}; font-size: 14px; font-weight: bold;
            letter-spacing: 2px; background: transparent;
        """)
        header.addWidget(title)
        header.addStretch()

        total = self.breach_data.get("total_breaches", 0)
        severity = "CRITICAL" if total >= 100 else "HIGH" if total >= 10 else "MODERATE" if total > 0 else "CLEAN"
        sev_lbl = QLabel(severity)
        sev_lbl.setStyleSheet(f"""
            background: {self.accent}20; color: {self.accent};
            border: 1px solid {self.accent}40; border-radius: 4px;
            padding: 2px 10px; font-size: 10px; font-weight: bold;
            letter-spacing: 1px;
        """)
        header.addWidget(sev_lbl)
        layout.addLayout(header)

        # ── Stats row ──
        stats = QHBoxLayout()
        stats.setSpacing(20)

        email = self.breach_data.get("email", "")
        email_lbl = QLabel(f"📧  {email}")
        email_lbl.setStyleSheet("color:#ccc; font-size:12px; background:transparent;")
        stats.addWidget(email_lbl)

        stats.addStretch()

        breach_count = QLabel(f"⚠  {total} breaches")
        breach_count.setStyleSheet(f"color:{self.accent}; font-size:13px; font-weight:bold; background:transparent;")
        stats.addWidget(breach_count)

        src_count = self.breach_data.get("total_sources", 0)
        sources_lbl = QLabel(f"📁  {src_count} sources")
        sources_lbl.setStyleSheet("color:#888; font-size:12px; background:transparent;")
        stats.addWidget(sources_lbl)
        layout.addLayout(stats)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color:{self.accent}33; max-height:1px; border:none;")
        layout.addWidget(sep)

        # ── Exposed fields ──
        fields = self.breach_data.get("fields_exposed", [])
        if fields:
            fields_row = QHBoxLayout()
            fields_row.setSpacing(4)
            fl = QLabel("EXPOSED:")
            fl.setStyleSheet("color:#555; font-size:9px; font-weight:bold; letter-spacing:1px; background:transparent;")
            fields_row.addWidget(fl)
            for f in fields[:12]:
                tag = QLabel(f.upper())
                danger = f.lower() in ("password", "ssn", "phone", "address", "dob", "ip")
                tag_color = "#ff0033" if danger else "#888"
                tag.setStyleSheet(f"""
                    background: {tag_color}15; color: {tag_color};
                    border: 1px solid {tag_color}30; border-radius: 3px;
                    padding: 1px 6px; font-size: 8px; font-weight: bold;
                """)
                fields_row.addWidget(tag)
            if len(fields) > 12:
                more = QLabel(f"+{len(fields)-12}")
                more.setStyleSheet("color:#555; font-size:9px; background:transparent;")
                fields_row.addWidget(more)
            fields_row.addStretch()
            layout.addLayout(fields_row)

        # ── Source list (scrollable) ──
        sources = self.breach_data.get("sources", [])
        if sources:
            src_header = QLabel(f"BREACH SOURCES ({len(sources)})")
            src_header.setStyleSheet(
                "color:#666; font-size:10px; font-weight:bold; "
                "letter-spacing:1px; background:transparent;"
            )
            layout.addWidget(src_header)

            # Show up to 15 sources
            src_grid = QGridLayout()
            src_grid.setSpacing(4)
            src_grid.setContentsMargins(0, 0, 0, 0)
            for i, s in enumerate(sources[:15]):
                name = s.get("name", "Unknown")
                date = s.get("date", "")

                name_lbl = QLabel(f"● {name}")
                name_lbl.setStyleSheet("color:#bbb; font-size:10px; background:transparent;")
                src_grid.addWidget(name_lbl, i, 0)

                if date:
                    date_lbl = QLabel(date)
                    date_lbl.setStyleSheet(
                        "color:#555; font-size:9px; background:transparent; "
                        "font-style:italic;"
                    )
                    date_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    src_grid.addWidget(date_lbl, i, 1)

            layout.addLayout(src_grid)

            if len(sources) > 15:
                more_lbl = QLabel(f"... and {len(sources) - 15} more sources")
                more_lbl.setStyleSheet("color:#555; font-size:10px; font-style:italic; background:transparent;")
                layout.addWidget(more_lbl)

        # ── Attribution (MANDATORY) ──
        attr_row = QHBoxLayout()
        attr_row.addStretch()
        attr_btn = QPushButton("Powered by LeakCheck")
        attr_btn.setObjectName("leakcheckAttr")
        attr_btn.setCursor(Qt.PointingHandCursor)
        attr_btn.setStyleSheet("""
            QPushButton#leakcheckAttr {
                background: transparent; border: none;
                color: #3399ff; font-size: 10px; font-weight: bold;
                text-decoration: underline; padding: 2px 4px;
            }
            QPushButton#leakcheckAttr:hover {
                color: #66bbff;
            }
        """)
        attr_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://leakcheck.io"))
        )
        attr_row.addWidget(attr_btn)
        layout.addLayout(attr_row)


# ══════════════════════════════════════════════════════════════
#  Enhanced Result Card (with profile pic, bio, buttons)
# ══════════════════════════════════════════════════════════════

class ResultCard(QFrame):
    """A styled card showing OSINT result with avatar, bio, stats, buttons."""

    CAT_COLORS = {"profile": "#00ff66", "document": "#ffaa00", "mention": "#8888aa"}

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result
        self.url = result.get("url", result.get("profile_url", ""))
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(380, 180)
        self.setMaximumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        cat = result.get("category", "mention")
        ac = self.CAT_COLORS.get(cat, "#888")
        self.accent = ac

        self.setStyleSheet(f"""
            ResultCard {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0c0c18, stop:1 #08080f);
                border: 1px solid #1a1a2e;
                border-left: 3px solid {ac};
                border-radius: 10px;
            }}
            ResultCard:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #10101f, stop:1 #0c0c18);
                border-color: {ac};
            }}
        """)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # ── Left: Profile picture ──
        pic_container = QVBoxLayout()
        pic_container.setAlignment(Qt.AlignTop)

        self.pic_label = QLabel()
        self.pic_label.setFixedSize(64, 64)
        self.pic_label.setAlignment(Qt.AlignCenter)

        # Try to load profile picture from data
        pic_data = self.result.get("profile_pic_data", b"")
        if pic_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(pic_data))
            if not pixmap.isNull():
                self.pic_label.setPixmap(make_circular_pixmap(pixmap, 64))
            else:
                self._set_initial_avatar()
        else:
            self._set_initial_avatar()

        pic_container.addWidget(self.pic_label)
        pic_container.addStretch()
        layout.addLayout(pic_container)

        # ── Right: Info column ──
        info = QVBoxLayout()
        info.setSpacing(4)

        # Platform badge + category
        badge_row = QHBoxLayout()
        platform = self.result.get("platform", self.result.get("source", "?"))
        badge = QLabel(platform.upper()[:20])
        badge.setStyleSheet(f"""
            background-color: {self.accent}20;
            color: {self.accent};
            border: 1px solid {self.accent}40;
            border-radius: 4px;
            padding: 2px 10px;
            font-size: 10px; font-weight: bold; letter-spacing: 1px;
        """)
        badge_row.addWidget(badge)

        # Verified badge
        if self.result.get("is_verified"):
            verified = QLabel("VERIFIED")
            verified.setStyleSheet(
                "background:#1a3300; color:#00ff66; border:1px solid #00ff6644; "
                "border-radius:3px; padding:1px 6px; font-size:9px; font-weight:bold;"
            )
            badge_row.addWidget(verified)

        badge_row.addStretch()
        cat = self.result.get("category", "mention")
        cat_lbl = QLabel(cat.upper())
        cat_lbl.setStyleSheet("color:#555; font-size:9px; letter-spacing:1px;")
        badge_row.addWidget(cat_lbl)
        info.addLayout(badge_row)

        # Username
        username = self.result.get("username", "")
        display_name = self.result.get("display_name", "")
        if display_name:
            name_lbl = QLabel(display_name)
            name_lbl.setStyleSheet(f"color:{self.accent}; font-size:13px; font-weight:bold;")
            info.addWidget(name_lbl)
        if username:
            user_lbl = QLabel(f"@{username}")
            user_lbl.setStyleSheet("color:#888; font-size:11px;")
            info.addWidget(user_lbl)

        # Bio
        bio = self.result.get("bio", "")
        if bio:
            bio_text = bio[:120] + "..." if len(bio) > 120 else bio
            bio_lbl = QLabel(bio_text)
            bio_lbl.setStyleSheet("color:#aaa; font-size:10px;")
            bio_lbl.setWordWrap(True)
            info.addWidget(bio_lbl)

        # Stats row (followers, repos, etc.)
        stats_parts = []
        if self.result.get("followers"):
            stats_parts.append(f"Followers: {self._fmt_num(self.result['followers'])}")
        if self.result.get("repos"):
            stats_parts.append(f"Repos: {self.result['repos']}")
        if self.result.get("posts"):
            stats_parts.append(f"Posts: {self._fmt_num(self.result['posts'])}")
        if self.result.get("karma"):
            stats_parts.append(f"Karma: {self._fmt_num(self.result['karma'])}")

        if stats_parts:
            stats_lbl = QLabel("  |  ".join(stats_parts))
            stats_lbl.setStyleSheet(f"color:{self.accent}; font-size:10px; font-weight:bold;")
            info.addWidget(stats_lbl)

        # URL (if no other info shown)
        if not username and not bio:
            display_url = self.url[:55] + "..." if len(self.url) > 55 else self.url
            url_lbl = QLabel(display_url)
            url_lbl.setStyleSheet("color:#3399ff; font-size:11px;")
            url_lbl.setWordWrap(True)
            info.addWidget(url_lbl)

        info.addStretch()

        # ── Bottom: separator + buttons ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color:#1a1a2e; max-height:1px; border:none;")
        info.addWidget(sep)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        view_btn = QPushButton("View Profile")
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.accent}15; color: {self.accent};
                border: 1px solid {self.accent}40; border-radius: 4px;
                padding: 4px 12px; font-size: 10px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.accent}; color: #000; }}
        """)
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.clicked.connect(lambda: self._open_url(self.url))
        btn_row.addWidget(view_btn)

        pic_url = self.result.get("profile_pic_url", "")
        if pic_url:
            dp_btn = QPushButton("View DP")
            dp_btn.setStyleSheet("""
                QPushButton {
                    background: #1a1a2e; color: #3399ff;
                    border: 1px solid #3399ff40; border-radius: 4px;
                    padding: 4px 12px; font-size: 10px; font-weight: bold;
                }
                QPushButton:hover { background: #3399ff; color: #000; }
            """)
            dp_btn.setCursor(Qt.PointingHandCursor)
            dp_btn.clicked.connect(lambda: self._open_url(pic_url))
            btn_row.addWidget(dp_btn)

        btn_row.addStretch()

        status = QLabel("\u25cf FOUND")
        status.setStyleSheet(f"color:{self.accent}; font-size:10px; font-weight:bold;")
        btn_row.addWidget(status)

        info.addLayout(btn_row)
        layout.addLayout(info, 1)

    def _set_initial_avatar(self):
        """Set a colored initial circle as the avatar."""
        platform = self.result.get("platform", self.result.get("source", "?"))
        initial = platform[0].upper() if platform else "?"
        self.pic_label.setText(initial)
        self.pic_label.setStyleSheet(f"""
            background-color: {self.accent}18;
            color: {self.accent};
            border: 2px solid {self.accent}88;
            border-radius: 32px;
            font-size: 24px; font-weight: bold;
        """)

    @staticmethod
    def _fmt_num(n) -> str:
        """Format large numbers: 1200 -> 1.2K"""
        try:
            n = int(n)
        except (ValueError, TypeError):
            return str(n)
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    def _open_url(self, url):
        if url and url.startswith("http"):
            QDesktopServices.openUrl(QUrl(url))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.url.startswith("http"):
            QDesktopServices.openUrl(QUrl(self.url))
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════════
#  Identity Cluster Card
# ══════════════════════════════════════════════════════════════

class IdentityCard(QFrame):
    """Card showing a cross-platform identity cluster."""

    def __init__(self, cluster: dict, parent=None):
        super().__init__(parent)
        self.cluster = cluster
        self.setMinimumSize(400, 160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        conf = cluster.get("confidence", 0)
        if conf >= 70:
            border_color = "#00ff66"
        elif conf >= 40:
            border_color = "#ffaa00"
        else:
            border_color = "#888"

        self.setStyleSheet(f"""
            IdentityCard {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0c0c18, stop:1 #08080f);
                border: 1px solid {border_color}44;
                border-top: 3px solid {border_color};
                border-radius: 10px;
            }}
        """)
        self._build(border_color)

    def _build(self, accent):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        # Profile pic
        pic_label = QLabel()
        pic_label.setFixedSize(56, 56)
        pic_label.setAlignment(Qt.AlignCenter)
        pic_data = self.cluster.get("profile_pic_data", b"")
        if pic_data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(pic_data))
            if not pixmap.isNull():
                pic_label.setPixmap(make_circular_pixmap(pixmap, 56))
            else:
                self._set_initial(pic_label, accent)
        else:
            self._set_initial(pic_label, accent)
        layout.addWidget(pic_label, 0, Qt.AlignTop)

        # Info
        info = QVBoxLayout()
        info.setSpacing(4)

        username = self.cluster.get("username", "?")
        conf = self.cluster.get("confidence", 0)
        header = QHBoxLayout()
        name_lbl = QLabel(f"IDENTITY: @{username}")
        name_lbl.setStyleSheet(f"color:{accent}; font-size:14px; font-weight:bold;")
        header.addWidget(name_lbl)
        header.addStretch()
        conf_lbl = QLabel(f"{conf}% CONFIDENCE")
        conf_color = accent
        conf_lbl.setStyleSheet(f"color:{conf_color}; font-size:11px; font-weight:bold;")
        header.addWidget(conf_lbl)
        info.addLayout(header)

        # Display name / bio
        display_name = self.cluster.get("enriched_data", {}).get("display_name", "")
        if display_name:
            dn_lbl = QLabel(display_name)
            dn_lbl.setStyleSheet("color:#ccc; font-size:12px;")
            info.addWidget(dn_lbl)

        bio = self.cluster.get("bio", "")
        if bio:
            bio_lbl = QLabel(bio[:100] + "..." if len(bio) > 100 else bio)
            bio_lbl.setStyleSheet("color:#888; font-size:10px;")
            bio_lbl.setWordWrap(True)
            info.addWidget(bio_lbl)

        # Platform tags
        platforms = self.cluster.get("platform_names", [])
        tag_row = QHBoxLayout()
        tag_row.setSpacing(6)
        for p in platforms[:8]:
            tag = QLabel(p)
            tag.setStyleSheet(f"""
                background: {accent}15; color: {accent};
                border: 1px solid {accent}30;
                border-radius: 3px; padding: 2px 8px;
                font-size: 9px; font-weight: bold;
            """)
            tag_row.addWidget(tag)
        if len(platforms) > 8:
            more = QLabel(f"+{len(platforms)-8} more")
            more.setStyleSheet("color:#555; font-size:9px;")
            tag_row.addWidget(more)
        tag_row.addStretch()
        info.addLayout(tag_row)

        layout.addLayout(info, 1)

    def _set_initial(self, label, accent):
        u = self.cluster.get("username", "?")
        label.setText(u[0].upper() if u else "?")
        label.setStyleSheet(f"""
            background-color: {accent}18; color: {accent};
            border: 2px solid {accent}88; border-radius: 28px;
            font-size: 22px; font-weight: bold;
        """)


# ══════════════════════════════════════════════════════════════
#  Card Scroll Area (grid of cards)
# ══════════════════════════════════════════════════════════════

class CardScrollArea(QWidget):
    """Scrollable area with a 2-column grid of ResultCards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll)

        self._cards = []
        self._count = 0
        self._cols = 2

    def add_result(self, result: dict):
        card = ResultCard(result)
        row = self._count // self._cols
        col = self._count % self._cols
        self.grid.addWidget(card, row, col)
        self._cards.append(card)
        self._count += 1

    def update_result(self, result: dict):
        """Replace an existing card with an updated (enriched) version."""
        url = result.get("url", "")
        for i, card in enumerate(self._cards):
            if isinstance(card, ResultCard) and card.url == url:
                # Remember grid position
                row = i // self._cols
                col = i % self._cols
                # Remove old card
                self.grid.removeWidget(card)
                card.setParent(None)
                card.deleteLater()
                # Create new enriched card
                new_card = ResultCard(result)
                self.grid.addWidget(new_card, row, col)
                self._cards[i] = new_card
                return True
        return False

    def add_identity(self, cluster: dict):
        """Add an identity cluster card (full width)."""
        card = IdentityCard(cluster)
        row = self._count // self._cols
        self.grid.addWidget(card, row, 0, 1, self._cols)  # span both columns
        self._cards.append(card)
        self._count += self._cols  # next row

    def add_breach(self, breach_data: dict):
        """Add a breach intelligence card (full width)."""
        card = BreachCard(breach_data)
        row = self._count // self._cols
        self.grid.addWidget(card, row, 0, 1, self._cols)  # span both columns
        self._cards.append(card)
        self._count += self._cols  # next row

    def clear_results(self):
        for c in self._cards:
            self.grid.removeWidget(c)
            c.setParent(None)
            c.deleteLater()
        self._cards.clear()
        self._count = 0

    def get_all_urls(self) -> list[str]:
        urls = []
        for c in self._cards:
            if isinstance(c, ResultCard) and c.url and c.url.startswith("http"):
                urls.append(c.url)
        return urls

    def filter_cards(self, text: str):
        t = text.lower()
        for c in self._cards:
            if isinstance(c, ResultCard):
                url = c.url.lower()
                plat = c.result.get("platform", "").lower()
                bio = c.result.get("bio", "").lower()
                c.setVisible(not t or t in url or t in plat or t in bio)
            elif isinstance(c, IdentityCard):
                u = c.cluster.get("username", "").lower()
                plats = " ".join(c.cluster.get("platform_names", [])).lower()
                c.setVisible(not t or t in u or t in plats)


# ══════════════════════════════════════════════════════════════
#  Utility Widgets
# ══════════════════════════════════════════════════════════════

class GlowSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(2)
        self.setStyleSheet("QFrame{background:#1a0008;border:none;max-height:2px;}")
        apply_glow(self, "#ff0033", 8)


class PulsingDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._op = 0.3
        self._grow = False
        self._active = False
        self._t = QTimer(self)
        self._t.timeout.connect(self._pulse)
        self._t.setInterval(50)

    def start(self):
        self._active = True; self._t.start(); self.update()

    def stop(self):
        self._active = False; self._t.stop(); self._op = 0.3; self.update()

    def _pulse(self):
        if self._grow:
            self._op = min(1.0, self._op + 0.05)
            if self._op >= 1.0: self._grow = False
        else:
            self._op = max(0.2, self._op - 0.05)
            if self._op <= 0.2: self._grow = True
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(255, 0, 51, int(255 * self._op)) if self._active else QColor(80, 80, 80, 80)
        p.setBrush(QBrush(c))
        p.setPen(Qt.NoPen)
        p.drawEllipse(3, 3, 10, 10)
        p.end()
