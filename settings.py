"""
Configuration settings for the Work Clock application.

You need to restart the app to apply any settings change.
"""

from pathlib import Path

# Where your saved log goes
SUMMARY_PATH = Path.home() / ".khanh_clock_summary.json"

# Application allowlist - apps where work time is tracked. You can see the current app in the bottom right of the app when it's running.
ALLOWLIST = {
    "Firefox",
    "Code",
    "Safari"
}

# Idle threshold in seconds
IDLE_THRESHOLD = 2

# Color settings
WORKING_COLOR = "#0077ff" 
INACTIVE_COLOR = "#aa0000"
TEXT_COLOR = "#f5f5f7" 


# Window settings
WINDOW_OPACITY = 0.9  # 0.0–1.0
WINDOW_WIDTH = 260
WINDOW_HEIGHT = 80
WINDOW_MARGIN_X = 20
WINDOW_MARGIN_Y = 60

# Update interval in milliseconds
UPDATE_INTERVAL = 1000

# Font settings
TIMER_FONT = ("Menlo", 20, "bold")
STATUS_FONT = ("Menlo", 9)
STATUS_FONT_BOLD = ("Menlo", 9, "bold")
