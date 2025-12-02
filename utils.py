"""
Utility functions for the Sith application.
"""

import subprocess
from typing import Optional
import json
import datetime
from pathlib import Path

try:
    from Cocoa import NSWorkspace
    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False


# Default configuration values
DEFAULT_CONFIG = {
    "allowlist": [
        "Sith",
    ],
    "idle_threshold": 2,
    "enable_color_animation": True,
    "time_display_style": "HH:MM:SS",  # Options: HH:MM:SS, HH:MM, Human Readable
    "colors": {
        "working": "#0077ff",
        "inactive": "#aa0000",
        "text": "#ffffff",
        "glass_working": "#00d4ff",
        "glass_inactive": "#ffffff"
    },
    "window": {
        "opacity": 0.9,
        "width": 260,
        "height": 80,
        "margin_x": 20,
        "margin_y": 60
    },
    "update_interval": 125,  # 1/8 second for faster updates
    "fonts": {
        "timer": ["Menlo", 20, "bold"],
        "status": ["Menlo", 9],
        "status_bold": ["Menlo", 9, "bold"]
    }
}

# Application directory in user's home
APP_DIR = Path.home() / ".sith"
CONFIG_PATH = APP_DIR / "config.json"
SUMMARY_PATH = APP_DIR / "summary.json"


def ensure_app_directory():
    """Create the application directory if it doesn't exist."""
    APP_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    """
    Load configuration from JSON file, creating default if needed.
    Returns the configuration dictionary.
    """
    ensure_app_directory()

    # Create default config if it doesn't exist
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
        print(f"Created default config at {CONFIG_PATH}")

    # Load and return config
    try:
        config = json.loads(CONFIG_PATH.read_text())
        # Merge with defaults to handle missing keys
        merged = DEFAULT_CONFIG.copy()
        merged.update(config)
        return merged
    except Exception as e:
        print(f"Error loading config: {e}, using defaults")
        return DEFAULT_CONFIG.copy()


def get_config():
    """Get configuration as an object-like interface."""
    config = load_config()

    class Config:
        ALLOWLIST = set(config.get("allowlist", DEFAULT_CONFIG["allowlist"]))
        IDLE_THRESHOLD = config.get("idle_threshold", DEFAULT_CONFIG["idle_threshold"])

        WORKING_COLOR = config.get("colors", {}).get("working", DEFAULT_CONFIG["colors"]["working"])
        INACTIVE_COLOR = config.get("colors", {}).get("inactive", DEFAULT_CONFIG["colors"]["inactive"])
        TEXT_COLOR = config.get("colors", {}).get("text", DEFAULT_CONFIG["colors"]["text"])
        GLASS_WORKING_COLOR = config.get("colors", {}).get("glass_working", DEFAULT_CONFIG["colors"]["glass_working"])
        GLASS_INACTIVE_COLOR = config.get("colors", {}).get("glass_inactive", DEFAULT_CONFIG["colors"]["glass_inactive"])

        WINDOW_OPACITY = config.get("window", {}).get("opacity", DEFAULT_CONFIG["window"]["opacity"])
        WINDOW_WIDTH = config.get("window", {}).get("width", DEFAULT_CONFIG["window"]["width"])
        WINDOW_HEIGHT = config.get("window", {}).get("height", DEFAULT_CONFIG["window"]["height"])
        WINDOW_MARGIN_X = config.get("window", {}).get("margin_x", DEFAULT_CONFIG["window"]["margin_x"])
        WINDOW_MARGIN_Y = config.get("window", {}).get("margin_y", DEFAULT_CONFIG["window"]["margin_y"])

        UPDATE_INTERVAL = config.get("update_interval", DEFAULT_CONFIG["update_interval"])

        TIMER_FONT = tuple(config.get("fonts", {}).get("timer", DEFAULT_CONFIG["fonts"]["timer"]))
        STATUS_FONT = tuple(config.get("fonts", {}).get("status", DEFAULT_CONFIG["fonts"]["status"]))
        STATUS_FONT_BOLD = tuple(config.get("fonts", {}).get("status_bold", DEFAULT_CONFIG["fonts"]["status_bold"]))

    return Config


def today_key() -> str:
    return datetime.date.today().isoformat()

def load_summary() -> dict:
    ensure_app_directory()

    if not SUMMARY_PATH.exists():
        return {}
    try:
        return json.loads(SUMMARY_PATH.read_text())
    except Exception:
        return {}

def save_summary(data: dict) -> None:
    ensure_app_directory()
    SUMMARY_PATH.write_text(json.dumps(data, indent=2))

def human_date(key: str) -> str:
    # "2025-12-01" -> "Dec 1, 2025"
    try:
        d = datetime.date.fromisoformat(key)
        return d.strftime("%b %-d, %Y")  # macOS supports %-d
    except Exception:
        return key


def get_idle_seconds() -> float:
    """
    Returns how many seconds since the last user input
    (mouse/keyboard) according to IOHIDSystem.
    """
    try:
        out = subprocess.check_output(
            ["ioreg", "-c", "IOHIDSystem"],
            text=True,
        )
        for line in out.splitlines():
            if "HIDIdleTime" in line:
                # HIDIdleTime = nanoseconds
                parts = line.split("=")
                if len(parts) == 2:
                    ns = int(parts[1].strip())
                    return ns / 1_000_000_000.0
    except Exception:
        pass
    return 0.0


def format_seconds(total: int, style: str = "HH:MM:SS") -> str:
    """
    Format seconds into various display formats.

    Styles:
    - HH:MM:SS: Standard format (01:23:45)
    - HH:MM: Hours and minutes only (01:23)
    - Human Readable: Compact with units (1h 23m or 23m 45s)
    """
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60

    if style == "HH:MM":
        return f"{hours:02d}:{minutes:02d}"
    elif style == "Human Readable":
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    else:  # Default to HH:MM:SS
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_frontmost_app_name() -> Optional[str]:
    """
    Get the name of the currently active (frontmost) application.
    Uses NSWorkspace to detect the active app on macOS.
    """
    if not PYOBJC_AVAILABLE:
        return None

    try:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        if active_app:
            # Get localized name (what user sees)
            app_name = active_app.localizedName()
            if app_name:
                return str(app_name)
        return None
    except Exception:
        return None


def format_date_short(date_str: str) -> str:
    """
    Format ISO date string to short format.
    Example: "2025-12-01" -> "Nov 21"
    """
    try:
        d = datetime.date.fromisoformat(date_str)
        return d.strftime("%b %-d")  # macOS supports %-d for no padding
    except Exception:
        return date_str


def generate_day_bar(seconds: int, max_seconds: int, max_width: int = 25) -> str:
    """
    Generate a horizontal bar chart for a day's work.

    Args:
        seconds: Total seconds worked this day
        max_seconds: Maximum seconds across all days (for scaling)
        max_width: Maximum width of the bar in characters

    Returns:
        String of █ characters representing the bar, or ─ for rest days
    """
    if seconds == 0:
        return "─"

    if max_seconds == 0:
        return ""

    # Calculate bar width proportional to max
    bar_width = int((seconds / max_seconds) * max_width)
    bar_width = max(1, min(bar_width, max_width))  # Clamp between 1 and max_width

    return "█" * bar_width


def generate_app_bar(app_seconds: int, day_total: int, max_width: int = 20) -> str:
    """
    Generate a horizontal bar chart for an app's time with percentage.

    Args:
        app_seconds: Seconds spent in this app
        day_total: Total seconds for the day
        max_width: Maximum width of the bar in characters

    Returns:
        String like "████████ (32%)" with bar and percentage
    """
    if day_total == 0 or app_seconds == 0:
        return "█ (0%)"

    # Calculate percentage
    percentage = int((app_seconds / day_total) * 100)

    # Calculate bar width
    bar_width = int((app_seconds / day_total) * max_width)
    bar_width = max(1, min(bar_width, max_width))  # At least 1, max max_width

    bar = "█" * bar_width
    return f"{bar} ({percentage}%)"


def generate_trend_chart(summary_data: dict, num_days: int = 14) -> str:
    """
    Generate a 14-day trend chart with Unicode box borders.

    Args:
        summary_data: Dictionary with date keys (ISO format) containing work data
        num_days: Number of days to show (default 14)

    Returns:
        Multi-line string with formatted trend chart
    """
    # Get last N days
    today = datetime.date.today()
    dates = []
    for i in range(num_days - 1, -1, -1):
        date = today - datetime.timedelta(days=i)
        dates.append(date.isoformat())

    # Collect data for each day
    day_data = []
    max_seconds = 0
    for date_str in dates:
        if date_str in summary_data and "total" in summary_data[date_str]:
            seconds = summary_data[date_str]["total"]
        else:
            seconds = 0
        day_data.append((date_str, seconds))
        max_seconds = max(max_seconds, seconds)

    # Build the chart
    lines = []
    chart_width = 46

    # Top border
    lines.append("╔" + "═" * (chart_width - 2) + "╗")

    # Title
    title = f"Last {num_days} Days Work Summary"
    padding = (chart_width - len(title) - 2) // 2
    lines.append("║" + " " * padding + title + " " * (chart_width - len(title) - padding - 2) + "║")

    # Separator
    lines.append("╠" + "═" * (chart_width - 2) + "╣")

    # Data rows
    today_str = today.isoformat()
    for date_str, seconds in day_data:
        date_short = format_date_short(date_str)
        bar = generate_day_bar(seconds, max_seconds, max_width=25)

        if seconds == 0:
            time_str = "(rest)"
        else:
            time_str = format_seconds(seconds, "HH:MM")

        # Format: "║ Nov 21  ████                        2:15     ║"
        # Build the row with proper spacing
        is_today = date_str == today_str
        today_marker = " ← Today" if is_today else ""

        # Calculate spacing to align everything
        bar_section = f"{bar:<25}"  # Bar left-aligned in 25 chars
        time_section = f"{time_str:>7}"  # Time right-aligned in 7 chars

        row = f"║ {date_short:6} {bar_section} {time_section}{today_marker}"

        # Pad to width
        current_len = len(row)
        padding_needed = chart_width - current_len - 1
        row += " " * padding_needed + "║"

        lines.append(row)

    # Bottom border
    lines.append("╚" + "═" * (chart_width - 2) + "╝")

    return "\n".join(lines)
