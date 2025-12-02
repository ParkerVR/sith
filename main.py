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
    WINDOW_OPACITY
)
from utils import *


class FrontAppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Work Clock")

        # Timer + summary state
        self.worked_seconds = 0
        self.is_working = False
        self.current_app = None
        self.summary = load_summary()
        self.today = today_key()

        # Initialize today's entry if needed
        if self.today not in self.summary:
            self.summary[self.today] = {"total": 0, "by_app": {}}

        # Always on top; native HUD vibe
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)  # borderless HUD

        # Window position (bottom-right)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - WINDOW_WIDTH - WINDOW_MARGIN_X
        y = screen_h - WINDOW_HEIGHT - WINDOW_MARGIN_Y
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        # Main background frame
        self.root.attributes("-alpha", WINDOW_OPACITY)

        self.frame = tk.Frame(self.root, bg=INACTIVE_COLOR, highlightthickness=0, bd=0)
        self.frame.pack(expand=True, fill="both")

        # --- Drag-to-move support ---
        self._drag_x = 0
        self._drag_y = 0
        self.frame.bind("<ButtonPress-1>", self._drag_start)
        self.frame.bind("<B1-Motion>", self._drag_move)

        # --- Timer text (center) ---
        self.timer_label = tk.Label(
            self.frame,
            text="00:00:00",
            font=TIMER_FONT,
            anchor="center",
            bg=INACTIVE_COLOR,
            fg=TEXT_COLOR,
        )
        self.timer_label.pack(expand=True, fill="both")

        # --- Bottom bar ---
        self.bottom_frame = tk.Frame(self.frame, bg=INACTIVE_COLOR, highlightthickness=0, bd=0)
        self.bottom_frame.pack(side="bottom", fill="x")

        self.app_label = tk.Label(
            self.bottom_frame,
            text="(starting...)",
            font=STATUS_FONT,
            anchor="w",
            padx=4,
            pady=2,
            bg=INACTIVE_COLOR,
            fg=TEXT_COLOR,
        )
        self.app_label.pack(side="left")

        self.status_label = tk.Label(
            self.bottom_frame,
            text="ACTIVE",
            font=STATUS_FONT_BOLD,
            anchor="e",
            padx=4,
            pady=2,
            bg=INACTIVE_COLOR,
            fg=TEXT_COLOR,
        )
        self.status_label.pack(side="right")

        # --- Right-click context menu ---
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label="Show Work Summary", command=self.show_summary_window)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.on_close)

        for widget in (self.frame, self.timer_label, self.bottom_frame,
                       self.app_label, self.status_label):
            widget.bind("<Button-2>", self._show_menu)
            widget.bind("<Button-3>", self._show_menu)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start update loop
        self.update_front_app()

    # ------------------------------------------------------------
    # Dragging the borderless HUD window
    # ------------------------------------------------------------
    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------
    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # ------------------------------------------------------------
    # Main loop: detect active app, idle state, update UI + timer
    # ------------------------------------------------------------
    def update_front_app(self):
        app_name = get_frontmost_app_name() or "(unknown)"
        idle_seconds = get_idle_seconds()
        allowed = app_name in ALLOWLIST
        is_idle = idle_seconds >= IDLE_THRESHOLD

        # Working only if app allowed AND user not idle
        self.is_working = allowed and not is_idle

        if self.is_working:
            self.worked_seconds += 1
            self.current_app = app_name

            # Update today's summary
            self.summary[self.today]["total"] += 1
            if app_name not in self.summary[self.today]["by_app"]:
                self.summary[self.today]["by_app"][app_name] = 0
            self.summary[self.today]["by_app"][app_name] += 1

        # Pick background
        bg = WORKING_COLOR if self.is_working else INACTIVE_COLOR
        status_text = "ACTIVE" if allowed and not is_idle else "IDLE"

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

        self.root.after(UPDATE_INTERVAL, self.update_front_app)

    # ------------------------------------------------------------
    # Summary persistence + shutdown
    # ------------------------------------------------------------
    def on_close(self):
        save_summary(self.summary)
        self.root.destroy()

    # ------------------------------------------------------------
    # Summary window
    # ------------------------------------------------------------
    def show_summary_window(self):
        win = tk.Toplevel(self.root)
        win.title("Work Summary")
        win.attributes("-topmost", True)
        win.geometry("380x400")
        win.configure(bg=INACTIVE_COLOR)

        header = tk.Label(
            win,
            text="Work Summary",
            font=TIMER_FONT,
            bg=INACTIVE_COLOR,
            fg=TEXT_COLOR,
            pady=5
        )
        header.pack()

        # Create a scrollable frame
        canvas = tk.Canvas(win, bg=INACTIVE_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=INACTIVE_COLOR)

        scrollable_frame.bind(
            "<Configure>",
            lambda _: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Sort entries by date (most recent first)
        for day in sorted(self.summary.keys(), reverse=True):
            day_data = self.summary[day]
            total_s = day_data["total"]
            by_app = day_data.get("by_app", {})

            # Date header with total
            row = tk.Frame(scrollable_frame, bg=INACTIVE_COLOR)
            row.pack(anchor="w", fill="x", pady=(8, 2))

            date_label = tk.Label(
                row,
                text=human_date(day),
                font=STATUS_FONT_BOLD if day == self.today else STATUS_FONT,
                bg=INACTIVE_COLOR,
                fg=TEXT_COLOR,
                width=14,
                anchor="w"
            )
            date_label.pack(side="left")

            time_label = tk.Label(
                row,
                text=format_seconds(total_s),
                font=STATUS_FONT_BOLD if day == self.today else STATUS_FONT,
                bg=INACTIVE_COLOR,
                fg=TEXT_COLOR,
                anchor="e"
            )
            time_label.pack(side="right", expand=True)

            # Per-app breakdown (indented)
            if by_app:
                for app_name in sorted(by_app.keys()):
                    app_seconds = by_app[app_name]

                    app_row = tk.Frame(scrollable_frame, bg=INACTIVE_COLOR)
                    app_row.pack(anchor="w", fill="x", padx=(20, 0), pady=1)

                    app_label = tk.Label(
                        app_row,
                        text=f"  {app_name}",
                        font=STATUS_FONT,
                        bg=INACTIVE_COLOR,
                        fg=TEXT_COLOR,
                        width=16,
                        anchor="w"
                    )
                    app_label.pack(side="left")

                    app_time_label = tk.Label(
                        app_row,
                        text=format_seconds(app_seconds),
                        font=STATUS_FONT,
                        bg=INACTIVE_COLOR,
                        fg=TEXT_COLOR,
                        anchor="e"
                    )
                    app_time_label.pack(side="right", expand=True)
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    window = FrontAppWindow()
    window.run()

