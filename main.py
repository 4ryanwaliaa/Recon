"""
╔══════════════════════════════════════════════════════════════╗
║   RECON — OSINT Intelligence Scanner                        ║
║   Entry Point                                               ║
║                                                              ║
║   Usage:  python main.py                                     ║
║                                                              ║
║   Environment Variables (optional):                          ║
║     SERPAPI_KEY  — SerpAPI key for Google dorking             ║
║     HIBP_API_KEY — HaveIBeenPwned API key                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import os

# Ensure project root is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtCore import Qt


def main():
    # High-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("RECON OSINT Scanner")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RECON")

    # Set default monospace font
    font_families = [
        "Cascadia Code", "Fira Code", "JetBrains Mono",
        "Consolas", "Courier New",
    ]
    for family in font_families:
        font = QFont(family, 10)
        if QFontDatabase.hasFamily(family):
            app.setFont(font)
            break
    else:
        app.setFont(QFont("Consolas", 10))

    # Launch the main window
    from gui.app import ReconApp
    window = ReconApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
