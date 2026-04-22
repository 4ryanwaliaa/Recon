"""
╔══════════════════════════════════════════════════════════════╗
║  Display Utilities — CLI fallback formatting helpers        ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import datetime


def timestamp() -> str:
    """Return the current timestamp string."""
    return datetime.now().strftime("%H:%M:%S")


def log_line(module: str, message: str) -> str:
    """Format a terminal-style log line."""
    return f"[{timestamp()}] [{module}] {message}"


def banner() -> str:
    """Return the ASCII art banner."""
    return r"""
 ██▀███  ▓█████  ▄████▄   ▒█████   ███▄    █ 
▓██ ▒ ██▒▓█   ▀ ▒██▀ ▀█  ▒██▒  ██▒ ██ ▀█   █ 
▓██ ░▄█ ▒▒███   ▒▓█    ▄ ▒██░  ██▒▓██  ▀█ ██▒
▒██▀▀█▄  ▒▓█  ▄ ▒▓▓▄ ▄██▒▒██   ██░▓██▒  ▐▌██▒
░██▓ ▒██▒░▒████▒▒ ▓███▀ ░░ ████▓▒░▒██░   ▓██░
░ ▒▓ ░▒▓░░░ ▒░ ░░ ░▒ ▒  ░░ ▒░▒░▒░ ░ ▒░   ▒ ▒ 
  ░▒ ░ ▒░ ░ ░  ░  ░  ▒     ░ ▒ ▒░ ░ ░░   ░ ▒░
  ░░   ░    ░   ░        ░ ░ ░ ▒     ░   ░ ░ 
   ░        ░  ░░ ░          ░ ░           ░  
                 ░                            
    [ RECON — OSINT Intelligence Scanner ]
"""


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """Generate an ASCII progress bar."""
    if total == 0:
        return "[" + " " * width + "]   0%"
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * current / total)
    return f"[{bar}] {pct:3d}%"
