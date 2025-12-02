import subprocess
import re
from typing import Optional

ALLOWLIST = {
    "Firefox",
}

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

import tkinter as tk

class FrontAppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Front App")

        # Always on top for HUD-style behavior
        self.root.attributes("-topmost", True)

        w, h = 260, 60
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - w - 20
        y = screen_h - h - 60
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.label = tk.Label(
            self.root,
            text="(starting...)",
            font=("Menlo", 14),
            anchor="center"
        )
        self.label.pack(expand=True, fill="both")

        self.update_front_app()

    def update_front_app(self):
        app_name = get_frontmost_app_name()
        if app_name is None:
            app_name = "(unknown)"

        # Update text
        self.label.config(text=app_name)

        # Determine allowed vs blocked
        if app_name in ALLOWLIST:
            bg = "#1fba2f"  # blue for allowed
        else:
            bg = "#aa0000"  # red for everything else

        # Apply background colors
        self.root.configure(bg=bg)
        self.label.configure(bg=bg)

        # Poll again in 1 second
        self.root.after(1000, self.update_front_app)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    #print(get_frontmost_app_name())
    window = FrontAppWindow()
    window.run()

