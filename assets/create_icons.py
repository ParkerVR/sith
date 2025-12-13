#!/usr/bin/env python3
"""
Script to create macOS icons from SVG files.
Converts SVG images to PNG at various sizes for status bar and app icons.
"""

from PIL import Image, ImageDraw
import cairosvg
import os
import io

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'generated')
STATUSBAR_SVG = os.path.join(SCRIPT_DIR, 'statusbar_icon.svg')
APP_ICON_SVG = os.path.join(SCRIPT_DIR, 'app_icon.svg')

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    # The SVG already contains the full app icon with gradient background
    # and rounded corners, so just convert it directly
    return svg_to_png(APP_ICON_SVG, size)

# Create status bar icons
print("Creating status bar icons...")
statusbar_1x = create_statusbar_icon(18)
statusbar_1x.save(os.path.join(OUTPUT_DIR, 'statusbar_icon.png'))

statusbar_2x = create_statusbar_icon(36)
statusbar_2x.save(os.path.join(OUTPUT_DIR, 'statusbar_icon@2x.png'))

print(f"Status bar icons created in {OUTPUT_DIR}/")

# Create app icon iconset
print("\nCreating app icon iconset...")
iconset_dir = os.path.join(OUTPUT_DIR, "AppIcon.iconset")
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
icns_path = os.path.join(OUTPUT_DIR, "AppIcon.icns")
try:
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path], check=True)
    print(f"✓ App icon created: {icns_path}")
except subprocess.CalledProcessError as e:
    print(f"✗ Failed to create .icns file: {e}")
    exit(1)

# Create App Store marketing assets
print("\nCreating App Store marketing assets...")
appstore_dir = os.path.join(OUTPUT_DIR, "appstore")
os.makedirs(appstore_dir, exist_ok=True)

# 1024x1024 app icon for App Store (no rounded corners, no alpha)
print("  Creating app_icon_1024.png (1024x1024)...")
app_icon_1024 = create_app_icon(1024)
# Convert to RGB (remove alpha) for App Store
app_icon_1024_rgb = Image.new('RGB', (1024, 1024), (255, 255, 255))
app_icon_1024_rgb.paste(app_icon_1024, (0, 0), app_icon_1024)
app_icon_1024_rgb.save(os.path.join(appstore_dir, 'app_icon_1024.png'))

print(f"\n✓ App Store assets created in {appstore_dir}/")

# Copy screenshots from assets/screenshots/ if they exist
screenshots_dir = os.path.join(SCRIPT_DIR, "screenshots")
if os.path.exists(screenshots_dir):
    print("\nCopying screenshots to App Store directory...")
    screenshot_mapping = {
        "app.png": "screenshot_main_2560x1600.png",
        "settings.png": "screenshot_settings_2560x1600.png"
    }

    import shutil
    for source_name, dest_name in screenshot_mapping.items():
        source_path = os.path.join(screenshots_dir, source_name)
        if os.path.exists(source_path):
            dest_path = os.path.join(appstore_dir, dest_name)
            shutil.copy2(source_path, dest_path)
            print(f"  Copied {source_name} → {dest_name}")
        else:
            print(f"  ⚠ {source_name} not found, skipping...")
    print(f"✓ Screenshots copied to {appstore_dir}/")
else:
    print("\nNote: Screenshots should be placed in assets/screenshots/")
