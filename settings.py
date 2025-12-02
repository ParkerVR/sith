"""
Configuration settings for the Work Clock application.
"""

# Application allowlist - apps where work time is tracked
ALLOWLIST = {
    "Firefox",
    "Code",
    "Safari"
}

# Idle threshold in seconds
IDLE_THRESHOLD = 10

# Color settings
WORKING_COLOR = "#0077ff"  # Blue - when actively working
INACTIVE_COLOR = "#aa0000"  # Red - when not working or idle
TEXT_COLOR = "white"

# Window settings
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
