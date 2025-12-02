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
    NSButton,
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

    # Add allowlist section
    label = create_label("App Allowlist:", 20, y_position, 150, 20)
    settings_window.contentView().addSubview_(label)

    y_position -= 25

    # Display each app with a remove button
    allowlist = current_config.get("allowlist", [])
    for app_name in allowlist:
        app_label = create_label(app_name, 30, y_position, 280, 20, font_size=10)
        settings_window.contentView().addSubview_(app_label)

        # Remove button - circular minus
        remove_btn = NSButton.alloc().initWithFrame_(NSMakeRect(315, y_position, 20, 20))
        remove_btn.setTitle_("-")
        remove_btn.setBezelStyle_(4)  # Circular bezel
        remove_btn.setFont_(NSFont.fontWithName_size_("Menlo", 12))
        settings_window.contentView().addSubview_(remove_btn)

        y_position -= 22

    y_position -= 15

    # Add section for recent apps
    add_label = create_label("Add app:", 20, y_position, 150, 20)
    settings_window.contentView().addSubview_(add_label)

    y_position -= 30

    # Get recent apps from summary (apps not in allowlist)
    from utils import load_summary
    summary = load_summary()
    recent_apps = set()
    for day_data in summary.values():
        if isinstance(day_data, dict) and "by_app" in day_data:
            recent_apps.update(day_data["by_app"].keys())

    # Filter out apps already in allowlist
    recent_apps = [app for app in recent_apps if app not in allowlist][:3]

    # Create buttons for recent apps
    x_pos = 20
    for app_name in recent_apps:
        add_btn = NSButton.alloc().initWithFrame_(NSMakeRect(x_pos, y_position, 100, 28))
        add_btn.setTitle_(app_name)
        add_btn.setBezelStyle_(1)
        add_btn.setFont_(NSFont.fontWithName_size_("Menlo", 9))
        settings_window.contentView().addSubview_(add_btn)
        x_pos += 110

    # Make sure window doesn't use our delegate
    settings_window.setDelegate_(None)

    # Set releasedWhenClosed to False to prevent crashes
    settings_window.setReleasedWhenClosed_(False)

    return settings_window, widgets
