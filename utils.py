"""
Utility functions for the Work Clock application.
"""

import subprocess
from typing import Optional
import json
import datetime
from ctypes import c_void_p
from settings import SUMMARY_PATH

try:
    from Cocoa import NSView, NSVisualEffectView, NSWorkspace
    import objc
    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False

def today_key() -> str:
    return datetime.date.today().isoformat()

def load_summary() -> dict:
    if not SUMMARY_PATH.exists():
        return {}
    try:
        return json.loads(SUMMARY_PATH.read_text())
    except Exception:
        return {}

def save_summary(data: dict) -> None:
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
    except Exception as e:
        print("Error in get_frontmost_app_name:", e)
        return None


def apply_glass_effect(tk_window) -> bool:
    """
    Apply native macOS vibrancy/glass effect to a tkinter window.
    Returns True if successful, False otherwise.

    This creates a beautiful frosted glass effect using NSVisualEffectView.
    """
    if not PYOBJC_AVAILABLE:
        print("PyObjC not available - glass effect disabled")
        return False

    try:
        from Cocoa import (
            NSApp,
            NSVisualEffectView,
            NSVisualEffectBlendingModeBehindWindow,
            NSVisualEffectMaterialHUDWindow,
        )
        import traceback

        print("Starting glass effect application...")

        # Get the native NSWindow from tkinter
        # tkinter uses a different approach - need to get through NSApp
        tk_window.update_idletasks()

        # Find the NSWindow by matching the title
        for window in NSApp.windows():
            if window.title() == tk_window.title():
                print(f"Found window: {window}")

                # Create NSVisualEffectView with HUD material (dark blur)
                content_view = window.contentView()
                if content_view is None:
                    print("No content view found")
                    return False

                bounds = content_view.bounds()
                print(f"Creating effect view with bounds: {bounds}")

                effect_view = NSVisualEffectView.alloc().initWithFrame_(bounds)

                # Configure the glass/vibrancy effect
                effect_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
                effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
                effect_view.setState_(1)  # Active state
                effect_view.setAutoresizingMask_(18)  # Flexible width and height (2|16)

                # Insert as the bottom-most layer
                content_view.addSubview_positioned_relativeTo_(
                    effect_view, -1, None
                )

                # Make the window background transparent so blur shows through
                from Cocoa import NSColor
                window.setBackgroundColor_(NSColor.clearColor())
                window.setOpaque_(False)

                print("Glass effect applied successfully!")
                return True

        print("Could not find window")
        return False

    except Exception as e:
        import traceback
        print(f"Failed to apply glass effect: {e}")
        traceback.print_exc()
        return False
