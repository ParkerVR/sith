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
)
from display_utils import add_glass_effect, create_label, create_text_field, hex_to_nscolor
from utils import load_config


def create_settings_window():
    """Create and return a settings window."""
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
    settings_window.settings_widgets = {}

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
    settings_window.settings_widgets['active_color'] = color_well

    y_position -= 50

    # Add idle timeout number field
    label = create_label("Idle timeout:", 20, y_position, 150, 20)
    settings_window.contentView().addSubview_(label)

    idle_field = create_text_field(str(current_config.get("idle_threshold", 2)), 180, y_position, 60, 22)
    settings_window.contentView().addSubview_(idle_field)
    settings_window.settings_widgets['idle_field'] = idle_field

    # Add unit selector dropdown
    unit_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(250, y_position - 2, 90, 26))
    unit_popup.addItemWithTitle_("seconds")
    unit_popup.addItemWithTitle_("minutes")
    unit_popup.addItemWithTitle_("hours")
    unit_popup.selectItemAtIndex_(0)  # Default to seconds
    settings_window.contentView().addSubview_(unit_popup)
    settings_window.settings_widgets['unit_popup'] = unit_popup

    # Make sure window doesn't use our delegate
    settings_window.setDelegate_(None)

    # Set releasedWhenClosed to False to prevent crashes
    settings_window.setReleasedWhenClosed_(False)

    return settings_window
