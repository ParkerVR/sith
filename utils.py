"""
Utility functions for the Sith application.
"""

import subprocess
from typing import Optional
import json
import datetime
from ctypes import c_void_p
from pathlib import Path

try:
    from Cocoa import NSView, NSVisualEffectView, NSWorkspace
    import objc
    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False


# Default configuration values
DEFAULT_CONFIG = {
    "allowlist": [
        "Firefox",
        "Code",
        "Safari"
    ],
    "idle_threshold": 2,
    "enable_color_animation": True,
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
    "update_interval": 1000,
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


def format_seconds(total: int) -> str:
    """
    Format seconds into HH:MM:SS format.
    """
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
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
