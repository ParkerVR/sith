"""
Work summary window for the Work Clock application.
"""

from Cocoa import (
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
    NSColor,
    NSFont,
    NSMakeRect,
)
from display_utils import add_glass_effect, create_label
from utils import format_seconds, human_date


def create_summary_window(summary_data, today_key):
    """Create and return a work summary window."""
    # Create summary window with close button
    summary_rect = NSMakeRect(100, 100, 380, 440)
    summary_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        summary_rect,
        NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
        NSBackingStoreBuffered,
        False,
    )

    # Configure window
    summary_window.setTitle_("Work Summary")
    summary_window.setLevel_(NSFloatingWindowLevel)
    summary_window.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.95))

    # Add glass effect
    add_glass_effect(summary_window)

    # Start from top of content area
    y_position = 380

    # Sort entries by date (most recent first)
    for day in sorted(summary_data.keys(), reverse=True):
        day_data = summary_data[day]
        total_s = day_data["total"]
        by_app = day_data.get("by_app", {})

        # Date header with total
        date_text = f"{human_date(day):14s} {format_seconds(total_s):>8s}"
        is_today = day == today_key

        date_label = create_label(
            date_text, 20, y_position, 340, 18,
            bold=is_today, font_size=10
        )
        summary_window.contentView().addSubview_(date_label)
        y_position -= 20

        # Per-app breakdown
        if by_app:
            for app_name in sorted(by_app.keys()):
                app_seconds = by_app[app_name]
                app_text = f"  {app_name:20s} {format_seconds(app_seconds):>8s}"

                app_label = create_label(app_text, 20, y_position, 340, 15, font_size=9)
                app_label.setTextColor_(
                    NSColor.colorWithCalibratedWhite_alpha_(0.9, 1.0)
                )
                summary_window.contentView().addSubview_(app_label)
                y_position -= 16

        y_position -= 8  # Extra space between days

    # Make sure summary window doesn't use our delegate
    summary_window.setDelegate_(None)

    # Set releasedWhenClosed to False to prevent crashes
    summary_window.setReleasedWhenClosed_(False)

    return summary_window
