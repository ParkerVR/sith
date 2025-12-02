"""
Utility functions for the Work Clock application.
"""

import subprocess
import re
from typing import Optional


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
    Uses lsappinfo to detect the active app on macOS.
    """
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
        print("Error in get_frontmost_app_name:", e)
        return None
