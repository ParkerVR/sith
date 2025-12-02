#!/usr/bin/env python3
"""
Create App Store assets for Sith time tracking app.
Generates screenshots, icons, and promotional materials.
"""

from PIL import Image, ImageDraw, ImageFont
import sys
import os

# Add parent directory to path to import from assets
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from create_icons import create_app_icon

def create_macos_window_mockup(width, height, title, content_draw_func):
    """Create a macOS window mockup with title bar."""
    img = Image.new('RGBA', (width, height), (245, 245, 247, 255))
    draw = ImageDraw.Draw(img)

    # macOS window with shadow
    window_x, window_y = 100, 100
    window_w = width - 200
    window_h = height - 200

    # Shadow
    shadow_offset = 20
    for i in range(shadow_offset):
        alpha = int((shadow_offset - i) / shadow_offset * 40)
        draw.rounded_rectangle(
            [window_x + i, window_y + i, window_x + window_w + i, window_y + window_h + i],
            radius=10,
            fill=(0, 0, 0, alpha)
        )

    # Window background
    draw.rounded_rectangle(
        [window_x, window_y, window_x + window_w, window_y + window_h],
        radius=10,
        fill=(255, 255, 255, 255)
    )

    # Title bar
    title_bar_height = 40
    draw.rounded_rectangle(
        [window_x, window_y, window_x + window_w, window_y + title_bar_height],
        radius=10,
        fill=(240, 240, 242, 255)
    )
    # Cover bottom corners of title bar to make it square
    draw.rectangle(
        [window_x, window_y + title_bar_height - 10, window_x + window_w, window_y + title_bar_height],
        fill=(240, 240, 242, 255)
    )

    # Traffic lights (close, minimize, maximize)
    button_y = window_y + 15
    button_x_start = window_x + 15
    button_spacing = 20
    colors = [(255, 95, 86), (255, 189, 68), (40, 205, 65)]  # Red, Yellow, Green
    for i, color in enumerate(colors):
        button_x = button_x_start + (i * button_spacing)
        draw.ellipse(
            [button_x, button_y, button_x + 12, button_y + 12],
            fill=color
        )

    # Window title
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", 14)
    except:
        title_font = ImageFont.load_default()

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = window_x + (window_w - title_width) // 2
    title_y = window_y + 12
    draw.text((title_x, title_y), title, fill=(0, 0, 0, 255), font=title_font)

    # Draw content area
    content_area = (window_x, window_y + title_bar_height, window_x + window_w, window_y + window_h)
    content_draw_func(img, content_area)

    return img


def draw_timer_window_content(img, area):
    """Draw the Sith timer window content."""
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = area

    # Background with gradient effect
    for y in range(y1, y2):
        ratio = (y - y1) / (y2 - y1)
        r = int(99 + (70 - 99) * ratio)
        g = int(102 + (80 - 102) * ratio)
        b = int(241 + (220 - 241) * ratio)
        draw.line([(x1, y), (x2, y)], fill=(r, g, b, 255))

    # Timer display
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    # Time text
    try:
        time_font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", 72)
        label_font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", 18)
    except:
        time_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    time_text = "2:45:30"
    time_bbox = draw.textbbox((0, 0), time_text, font=time_font)
    time_width = time_bbox[2] - time_bbox[0]
    time_height = time_bbox[3] - time_bbox[1]

    draw.text(
        (center_x - time_width // 2, center_y - time_height // 2 - 40),
        time_text,
        fill=(255, 255, 255, 255),
        font=time_font
    )

    # Status label
    status_text = "Working"
    status_bbox = draw.textbbox((0, 0), status_text, font=label_font)
    status_width = status_bbox[2] - status_bbox[0]

    draw.text(
        (center_x - status_width // 2, center_y + 60),
        status_text,
        fill=(255, 255, 255, 200),
        font=label_font
    )


def draw_settings_window_content(img, area):
    """Draw the settings window content."""
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = area
    padding = 30

    try:
        header_font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", 24)
        label_font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", 14)
    except:
        header_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    # Header
    draw.text((x1 + padding, y1 + padding), "Settings", fill=(0, 0, 0, 255), font=header_font)

    # Settings items
    y_pos = y1 + padding + 50
    items = [
        "Allowed Apps:",
        "  • Visual Studio Code",
        "  • Terminal",
        "  • Xcode",
        "",
        "Idle Threshold: 60 seconds",
        "Update Interval: 1 second",
        "",
        "Colors:",
        "  Working: Indigo",
        "  Inactive: Gray"
    ]

    for item in items:
        draw.text((x1 + padding, y_pos), item, fill=(0, 0, 0, 200), font=label_font)
        y_pos += 25


def create_screenshot_with_statusbar(width, height):
    """Create a screenshot showing the status bar icon."""
    img = Image.new('RGBA', (width, height), (245, 245, 247, 255))
    draw = ImageDraw.Draw(img)

    # macOS menu bar
    menubar_height = 30
    draw.rectangle([0, 0, width, menubar_height], fill=(240, 240, 242, 255))

    # Apple logo area (placeholder)
    draw.text((15, 7), "", fill=(0, 0, 0, 255))  # Apple symbol

    # Status bar icon on the right
    icon_size = 18
    icon_x = width - 100
    icon_y = (menubar_height - icon_size) // 2

    # Draw a simple clock icon
    draw.ellipse(
        [icon_x, icon_y, icon_x + icon_size, icon_y + icon_size],
        outline=(0, 0, 0, 255),
        width=2
    )
    # Clock hands
    center_x = icon_x + icon_size // 2
    center_y = icon_y + icon_size // 2
    draw.line([(center_x, center_y), (center_x, center_y - 5)], fill=(0, 0, 0, 255), width=2)
    draw.line([(center_x, center_y), (center_x + 4, center_y)], fill=(0, 0, 0, 255), width=2)

    # Draw main window below
    draw_timer_window_content(img, (100, menubar_height + 50, width - 100, height - 50))

    return img


def create_hero_image(width, height):
    """Create a hero/promotional image."""
    img = Image.new('RGBA', (width, height), (99, 102, 241, 255))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(99 + (139 - 99) * ratio)
        g = int(102 + (92 - 102) * ratio)
        b = int(241 + (246 - 241) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # App icon in the center
    icon_size = 200
    icon = create_app_icon(icon_size)
    icon_x = (width - icon_size) // 2
    icon_y = height // 3 - icon_size // 2
    img.paste(icon, (icon_x, icon_y), icon)

    # Title and tagline
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", 64)
        tagline_font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()

    title = "Sith"
    tagline = "Focus. Track. Achieve."

    # Draw title
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(
        ((width - title_width) // 2, icon_y + icon_size + 40),
        title,
        fill=(255, 255, 255, 255),
        font=title_font
    )

    # Draw tagline
    tagline_bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_width = tagline_bbox[2] - tagline_bbox[0]
    draw.text(
        ((width - tagline_width) // 2, icon_y + icon_size + 120),
        tagline,
        fill=(255, 255, 255, 200),
        font=tagline_font
    )

    return img


print("Creating App Store assets...")

# 1. App Store Icon (1024x1024)
print("  Creating App Store icon (1024x1024)...")
app_store_icon = create_app_icon(1024)
app_store_icon.save('app_icon_1024.png')
print("    ✓ app_icon_1024.png")

# 2. macOS App Store Screenshots (various sizes)
screenshot_sizes = [
    (2880, 1800, "screenshot_2880x1800.png"),
    (2560, 1600, "screenshot_2560x1600.png"),
    (1440, 900, "screenshot_1440x900.png"),
    (1280, 800, "screenshot_1280x800.png"),
]

print("  Creating screenshots...")
for width, height, filename in screenshot_sizes:
    print(f"    Creating {filename}...")
    screenshot = create_macos_window_mockup(width, height, "Sith", draw_timer_window_content)
    screenshot.save(filename)
    print(f"    ✓ {filename}")

# 3. Settings window screenshot
print("  Creating settings screenshot...")
settings_screenshot = create_macos_window_mockup(2560, 1600, "Sith - Settings", draw_settings_window_content)
settings_screenshot.save('screenshot_settings_2560x1600.png')
print("    ✓ screenshot_settings_2560x1600.png")

# 4. Hero/Promotional image
print("  Creating hero image...")
hero = create_hero_image(2560, 1440)
hero.save('hero_2560x1440.png')
print("    ✓ hero_2560x1440.png")

# 5. Preview image (smaller for web)
print("  Creating preview image...")
preview = create_hero_image(1200, 675)
preview.save('preview_1200x675.png')
print("    ✓ preview_1200x675.png")

print("\n✓ All App Store assets created successfully!")
print(f"Assets saved to: {os.getcwd()}")
