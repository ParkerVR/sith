"""
Settings window for the Work Clock application.
"""

from Cocoa import (
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
    NSColor,
    NSColorWell,
    NSPopUpButton,
    NSMakeRect,
    NSFont,
    NSTextView,
    NSScrollView,
)
from display_utils import add_glass_effect, create_label, create_text_field, hex_to_nscolor
from utils import load_config


def create_settings_window():
    """Create and return a settings window and its widgets.

    Returns:
        tuple: (settings_window, widgets_dict)
    """
    # Create window with close button
    settings_rect = NSMakeRect(100, 100, 380, 440)
    settings_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        settings_rect,
        NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
        NSBackingStoreBuffered,
        False,
    )

    # Configure window
    settings_window.setTitle_("Settings")
    settings_window.setLevel_(NSFloatingWindowLevel)
    settings_window.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.95))

    # Add glass effect
    add_glass_effect(settings_window)

    # Load current config
    current_config = load_config()

    # Store widgets for saving later
    widgets = {}

    # Start with simple text
    y_position = 380

    hello_label = create_label("Settings", 20, y_position, 340, 25, bold=True, font_size=18)
    settings_window.contentView().addSubview_(hello_label)

    y_position -= 40

    # Add color picker
    label = create_label("Active text color:", 20, y_position, 150, 20)
    settings_window.contentView().addSubview_(label)

    color_well = NSColorWell.alloc().initWithFrame_(NSMakeRect(180, y_position, 60, 25))
    active_color = hex_to_nscolor(current_config.get("colors", {}).get("glass_working", "#00d4ff"))
    color_well.setColor_(active_color)
    settings_window.contentView().addSubview_(color_well)
    widgets['active_color'] = color_well

    y_position -= 50

    # Add idle timeout number field
    label = create_label("Idle timeout:", 20, y_position, 150, 20)
    settings_window.contentView().addSubview_(label)

    idle_field = create_text_field(str(current_config.get("idle_threshold", 2)), 180, y_position, 60, 22)
    settings_window.contentView().addSubview_(idle_field)
    widgets['idle_field'] = idle_field

    # Add unit selector dropdown
    unit_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(250, y_position - 2, 90, 26))
    unit_popup.addItemWithTitle_("seconds")
    unit_popup.addItemWithTitle_("minutes")
    unit_popup.addItemWithTitle_("hours")
    unit_popup.selectItemAtIndex_(0)  # Default to seconds
    settings_window.contentView().addSubview_(unit_popup)
    widgets['unit_popup'] = unit_popup

    y_position -= 50

    # Add allowlist text field - one app per line
    label = create_label("App Allowlist:", 20, y_position, 150, 20)
    settings_window.contentView().addSubview_(label)

    # Join allowlist apps with newlines
    allowlist = current_config.get("allowlist", [])
    allowlist_text = "\n".join(allowlist)

    # Create multi-line text field
    scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, y_position - 80, 320, 70))
    scroll_view.setHasVerticalScroller_(True)
    scroll_view.setBorderType_(1)  # NSBezelBorder

    text_view = NSTextView.alloc().initWithFrame_(scroll_view.contentView().bounds())
    text_view.setString_(allowlist_text)
    text_view.setFont_(NSFont.fontWithName_size_("Menlo", 10))
    text_view.setTextColor_(NSColor.whiteColor())
    text_view.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.8))

    scroll_view.setDocumentView_(text_view)
    settings_window.contentView().addSubview_(scroll_view)
    widgets['allowlist_text'] = text_view

    # Make sure window doesn't use our delegate
    settings_window.setDelegate_(None)

    # Set releasedWhenClosed to False to prevent crashes
    settings_window.setReleasedWhenClosed_(False)

    return settings_window, widgets
