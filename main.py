"""
Work Clock - Main application window and entry point.
Tracks time spent in allowed applications and displays it in a floating window.
"""

import tkinter as tk
from settings import (
    ALLOWLIST,
    IDLE_THRESHOLD,
    WORKING_COLOR,
    INACTIVE_COLOR,
    TEXT_COLOR,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MARGIN_X,
    WINDOW_MARGIN_Y,
    UPDATE_INTERVAL,
    TIMER_FONT,
    STATUS_FONT,
    STATUS_FONT_BOLD,
)
from utils import get_idle_seconds, get_frontmost_app_name, format_seconds

class FrontAppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Work Clock")

        # Timer state
        self.worked_seconds = 0
        self.is_working = False

        # Always on top
        self.root.attributes("-topmost", True)

        # Calculate window position (bottom-right corner)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - WINDOW_WIDTH - WINDOW_MARGIN_X
        y = screen_h - WINDOW_HEIGHT - WINDOW_MARGIN_Y
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        # Main frame for background color
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill="both")

        # Big timer in the middle
        self.timer_label = tk.Label(
            self.frame,
            text="00:00:00",
            font=TIMER_FONT,
            anchor="center"
        )
        self.timer_label.pack(expand=True, fill="both")

        # Bottom bar: app name (left) + status (right)
        self.bottom_frame = tk.Frame(self.frame)
        self.bottom_frame.pack(side="bottom", fill="x")

        self.app_label = tk.Label(
            self.bottom_frame,
            text="(starting...)",
            font=STATUS_FONT,
            anchor="w",
            padx=4,
            pady=2,
        )
        self.app_label.pack(side="left")

        self.status_label = tk.Label(
            self.bottom_frame,
            text="ACTIVE",
            font=STATUS_FONT_BOLD,
            anchor="e",
            padx=4,
            pady=2,
        )
        self.status_label.pack(side="right")

        self.update_front_app()

    def update_front_app(self):
        app_name = get_frontmost_app_name()
        if app_name is None:
            app_name = "(unknown)"

        idle_seconds = get_idle_seconds()
        allowed = app_name in ALLOWLIST
        is_idle = idle_seconds >= IDLE_THRESHOLD

        # Working only if app is allowed AND not idle
        self.is_working = allowed and not is_idle

        if self.is_working:
            self.worked_seconds += 1

        # Background: working color when active, inactive color otherwise
        bg = WORKING_COLOR if self.is_working else INACTIVE_COLOR

        status_text = "ACTIVE" if not is_idle and allowed else "IDLE"

        # Update UI
        self.root.configure(bg=bg)
        self.frame.configure(bg=bg)
        self.bottom_frame.configure(bg=bg)

        self.timer_label.configure(
            text=format_seconds(self.worked_seconds),
            bg=bg,
            fg=TEXT_COLOR,
        )
        self.app_label.configure(
            text=app_name,
            bg=bg,
            fg=TEXT_COLOR,
        )
        self.status_label.configure(
            text=status_text,
            bg=bg,
            fg=TEXT_COLOR,
        )

        # Poll again after UPDATE_INTERVAL
        self.root.after(UPDATE_INTERVAL, self.update_front_app)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    window = FrontAppWindow()
    window.run()

