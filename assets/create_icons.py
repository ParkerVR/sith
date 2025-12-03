#!/usr/bin/env python3
"""
Script to create macOS icons from SVG files.
Converts SVG images to PNG at various sizes for status bar and app icons.
"""

from PIL import Image
import cairosvg
import os
import io

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATUSBAR_SVG = os.path.join(SCRIPT_DIR, 'statusbar_icon.svg')
APP_ICON_SVG = os.path.join(SCRIPT_DIR, 'app_icon.svg')

def svg_to_png(svg_path, size):
    """Convert SVG file to PNG at the specified size and return as PIL Image."""
    # Convert SVG to PNG bytes using cairosvg
    png_data = cairosvg.svg2png(
        url=svg_path,
        output_width=size,
        output_height=size
    )

    # Load PNG data into PIL Image
    img = Image.open(io.BytesIO(png_data))
    return img

def create_statusbar_icon(size):
    """Create status bar icon from SVG at the specified size."""
    return svg_to_png(STATUSBAR_SVG, size)

def create_app_icon(size):
    """Create app icon from SVG at the specified size."""
    # For the app icon, we need to add the colorful background and styling
    # Load the base clock SVG
    clock_img = svg_to_png(APP_ICON_SVG, size)

    # Create a new image with gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    corner_radius = int(size * 0.22)  # macOS icon corner radius

    # Draw rounded rectangle background with gradient effect
    # Top color: #6366f1 (indigo), Bottom color: #8b5cf6 (violet)
    for y in range(size):
        ratio = y / size
        r = int(99 + (139 - 99) * ratio)
        g = int(102 + (92 - 102) * ratio)
        b = int(241 + (246 - 241) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Create rounded corners mask
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=corner_radius,
        fill=255
    )

    # Apply mask to background
    img.putalpha(mask)

    # Resize and center the clock icon
    icon_size = int(size * 0.6)  # Clock takes up 60% of the icon
    clock_resized = clock_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    # Calculate position to center the clock
    x = (size - icon_size) // 2
    y = (size - icon_size) // 2

    # Composite the clock onto the background
    img.paste(clock_resized, (x, y), clock_resized)

    return img

# Create status bar icons
print("Creating status bar icons...")
statusbar_1x = create_statusbar_icon(18)
statusbar_1x.save('statusbar_icon.png')

statusbar_2x = create_statusbar_icon(36)
statusbar_2x.save('statusbar_icon@2x.png')

print("Status bar icons created: statusbar_icon.png, statusbar_icon@2x.png")

# Create app icon iconset
print("\nCreating app icon iconset...")
iconset_dir = "AppIcon.iconset"
os.makedirs(iconset_dir, exist_ok=True)

# Required sizes for macOS app icons
sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

for size, filename in sizes:
    output_path = os.path.join(iconset_dir, filename)
    print(f"  Creating {filename} ({size}x{size})...")
    icon = create_app_icon(size)
    icon.save(output_path)

print(f"\nIconset created at {iconset_dir}/")
print("Converting to .icns format...")

# Convert iconset to .icns using macOS iconutil
import subprocess
icns_path = "AppIcon.icns"
try:
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path], check=True)
    print(f"✓ App icon created: {icns_path}")
except subprocess.CalledProcessError as e:
    print(f"✗ Failed to create .icns file: {e}")
    exit(1)
