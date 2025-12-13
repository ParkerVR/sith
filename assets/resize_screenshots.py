#!/usr/bin/env python3
"""
Resize screenshots for App Store submission.
Converts screenshots to 2880x1800 (macOS Retina 5K display size).
"""

from PIL import Image
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, 'screenshots')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'generated', 'appstore', 'screenshots')

# Target size for App Store (2880x1800 - Retina 5K)
TARGET_WIDTH = 2880
TARGET_HEIGHT = 1800

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Resizing screenshots from {INPUT_DIR}...")
print(f"Target size: {TARGET_WIDTH}x{TARGET_HEIGHT}")
print()

# Find all PNG files in screenshots directory
screenshot_files = sorted([f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.png')])

if not screenshot_files:
    print("No PNG files found in screenshots directory!")
    exit(1)

for i, filename in enumerate(screenshot_files, 1):
    input_path = os.path.join(INPUT_DIR, filename)
    output_filename = f"screenshot_{i}_2880x1800.png"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    print(f"Processing {filename}...")

    try:
        # Open image
        img = Image.open(input_path)
        original_size = img.size
        print(f"  Original size: {original_size[0]}x{original_size[1]}")

        # Resize using high-quality Lanczos resampling
        img_resized = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

        # Save as PNG
        img_resized.save(output_path, 'PNG', optimize=True)
        print(f"  ✓ Saved as {output_filename}")
        print()

    except Exception as e:
        print(f"  ✗ Error: {e}")
        print()

print(f"✓ All screenshots resized and saved to:")
print(f"  {OUTPUT_DIR}")
