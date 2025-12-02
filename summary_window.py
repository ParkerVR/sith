"""
Work summary window for the Sith application.
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
    NSScrollView,
    NSTextView,
)
from display_utils import add_glass_effect
from utils import format_seconds, human_date, generate_app_bar


def create_summary_window(summary_data, today_key):
    """Create and return a work summary window."""
    # Create summary window with close button
    summary_rect = NSMakeRect(100, 100, 420, 500)
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

    # Create scroll view for content
    scroll_rect = summary_window.contentView().bounds()
    scroll_view = NSScrollView.alloc().initWithFrame_(scroll_rect)
    scroll_view.setHasVerticalScroller_(True)
    scroll_view.setHasHorizontalScroller_(False)
    scroll_view.setAutoresizingMask_(18)
    scroll_view.setDrawsBackground_(False)

    # Create text view for summary content
    text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 400, 2000))
    text_view.setEditable_(False)
    text_view.setSelectable_(True)
    text_view.setBackgroundColor_(NSColor.clearColor())
    text_view.setTextColor_(NSColor.whiteColor())
    text_view.setFont_(NSFont.fontWithName_size_("Menlo", 10))

    # Build summary text
    lines = []

    # Check if there's any data
    if not summary_data:
        lines.append("No work data recorded yet.")
        lines.append("")
        lines.append("Start using tracked apps to see your work summary here!")
    else:
        # Sort entries by date (most recent first)
        for day in sorted(summary_data.keys(), reverse=True):
            day_data = summary_data[day]
            total_s = day_data.get("total", 0)
            by_app = day_data.get("by_app", {})

            # Date header with total (no inline bar)
            date_line = f"{human_date(day):17s} {format_seconds(int(total_s)):>8s}"
            lines.append(date_line)

            # Per-app breakdown with bars
            if by_app:
                # Sort by time (descending) to show most used apps first
                sorted_apps = sorted(by_app.items(), key=lambda x: x[1], reverse=True)
                for app_name, app_seconds in sorted_apps:
                    bar_with_pct = generate_app_bar(int(app_seconds), int(total_s), max_width=16)
                    app_line = f"  {app_name:20s} {format_seconds(int(app_seconds)):>8s}  {bar_with_pct}"
                    lines.append(app_line)

            lines.append("")  # Empty line between days

    summary_text = "\n".join(lines)
    text_view.setString_(summary_text)

    scroll_view.setDocumentView_(text_view)
    summary_window.contentView().addSubview_(scroll_view)

    # Make sure summary window doesn't use our delegate
    summary_window.setDelegate_(None)

    # Set releasedWhenClosed to False to prevent crashes
    summary_window.setReleasedWhenClosed_(False)

    return summary_window
