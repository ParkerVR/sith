import subprocess
import re
from typing import Optional
import tkinter as tk


ALLOWLIST = {
    "Firefox",
    "Code",
    "Safari"
}

IDLE_THRESHOLD = 10  # seconds


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
    except Exception as e:
        print("Error in get_idle_seconds:", e)
    return 0.0

def format_seconds(total: int) -> str:
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_frontmost_app_name() -> Optional[str]:
    try:
        # 1) Get the ASN of the frontmost app, e.g. "ASN:0x0-f5e25d3:"
        asn_line = subprocess.check_output(
            ["lsappinfo", "front"],
            text=True
        ).strip()

        # 2) Extract the hex part after the dash
        m = re.search(r"ASN:0x0-(?:0x)?([0-9a-fA-F]+):", asn_line)
        if not m:
            return None

        hex_part = m.group(1)
        # Sonoma quirk: lsappinfo info expects "ASN:0x0-0x<hex>:"
        asn_fixed = f"ASN:0x0-0x{hex_part}:"

        # 3) Ask lsappinfo for the name for that ASN
        info_out = subprocess.check_output(
            ["lsappinfo", "info", "-only", "name", asn_fixed],
            text=True
        )

        # Output looks like: '"LSDisplayName"="iTerm2"'
        m2 = re.search(r'"(?:LSDisplayName|Name)"="([^"]+)"', info_out)
        if m2:
            return m2.group(1)

        return None

    except Exception as e:
        # Optional: log / print for debugging, but return None so the rest of your app doesn't crash
        print("Error in get_frontmost_app_name:", e)
        return None

class FrontAppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Work Clock")

        # Timer state
        self.worked_seconds = 0
        self.is_working = False

        # Always on top
        self.root.attributes("-topmost", True)

        w, h = 260, 80
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - w - 20
        y = screen_h - h - 60
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Main frame for background color
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill="both")

        # Big timer in the middle
        self.timer_label = tk.Label(
            self.frame,
            text="00:00:00",
            font=("Menlo", 20, "bold"),
            anchor="center"
        )
        self.timer_label.pack(expand=True, fill="both")

        # Bottom bar: app name (left) + status (right)
        self.bottom_frame = tk.Frame(self.frame)
        self.bottom_frame.pack(side="bottom", fill="x")

        self.app_label = tk.Label(
            self.bottom_frame,
            text="(starting...)",
            font=("Menlo", 9),
            anchor="w",
            padx=4,
            pady=2,
        )
        self.app_label.pack(side="left")

        self.status_label = tk.Label(
            self.bottom_frame,
            text="ACTIVE",
            font=("Menlo", 9, "bold"),
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

        # Background: blue when actually working, red otherwise
        bg = "#0077ff" if self.is_working else "#aa0000"

        status_text = "ACTIVE" if not is_idle and allowed else "IDLE"

        # Update UI
        self.root.configure(bg=bg)
        self.frame.configure(bg=bg)
        self.bottom_frame.configure(bg=bg)

        self.timer_label.configure(
            text=format_seconds(self.worked_seconds),
            bg=bg,
            fg="white",
        )
        self.app_label.configure(
            text=app_name,
            bg=bg,
            fg="white",
        )
        self.status_label.configure(
            text=status_text,
            bg=bg,
            fg="white",
        )

        # Poll again in 1 second
        self.root.after(1000, self.update_front_app)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    #print(get_frontmost_app_name())
    window = FrontAppWindow()
    window.run()

