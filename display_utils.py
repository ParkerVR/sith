"""
Shared display utilities for the Sith application.
"""

from Cocoa import (
    NSColor,
    NSTextField,
    NSFont,
    NSFontWeightRegular,
    NSFontWeightBold,
    NSFontWeightMedium,
    NSMakeRect,
    NSVisualEffectView,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialHUDWindow,
)


def hex_to_nscolor(hex_color):
    """Convert hex color string to NSColor."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0)


def nscolor_to_hex(color):
    """Convert NSColor to hex string."""
    # Convert to RGB color space
    rgb_color = color.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
    if rgb_color:
        r = int(rgb_color.redComponent() * 255)
        g = int(rgb_color.greenComponent() * 255)
        b = int(rgb_color.blueComponent() * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    return "#ffffff"


def add_glass_effect(window):
    """Add glass/vibrancy effect to a window."""
    effect_view = NSVisualEffectView.alloc().initWithFrame_(
        window.contentView().bounds()
    )
    effect_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
    effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
    effect_view.setState_(1)
    effect_view.setAutoresizingMask_(18)
    window.contentView().addSubview_(effect_view)


def get_font(font_family, size, bold=False):
    """
    Get NSFont based on font family preference.

    Args:
        font_family: "SF Pro", "SF Mono", or "Menlo"
        size: Font size in points
        bold: Whether to use bold weight

    Returns:
        NSFont instance
    """
    weight = NSFontWeightBold if bold else NSFontWeightRegular

    if font_family == "SF Mono":
        # Use monospaced system font
        return NSFont.monospacedSystemFontOfSize_weight_(size, weight)
    elif font_family == "Menlo":
        # Use Menlo (legacy monospace)
        font_name = "Menlo-Bold" if bold else "Menlo"
        return NSFont.fontWithName_size_(font_name, size) or NSFont.systemFontOfSize_weight_(size, weight)
    else:  # SF Pro (default)
        # Use system font (San Francisco)
        if bold:
            return NSFont.boldSystemFontOfSize_(size)
        else:
            return NSFont.systemFontOfSize_(size)


def create_label(text, x, y, w, h, bold=False, font_size=11, font_family="SF Pro"):
    """Create a standard label with common settings."""
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    label.setStringValue_(text)
    label.setFont_(get_font(font_family, font_size, bold))
    label.setTextColor_(NSColor.whiteColor())
    label.setBackgroundColor_(NSColor.clearColor())
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    return label


def create_text_field(value, x, y, w, h, font_size=12, font_family="SF Pro"):
    """Create a text input field with dark background and white text."""
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    field.setStringValue_(value)
    field.setFont_(get_font(font_family, font_size, False))
    field.setTextColor_(NSColor.whiteColor())
    field.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.8))
    field.setDrawsBackground_(True)
    return field
