#!/usr/bin/env python3
"""
Script to create macOS icons using Pillow.
Creates PNG images for the status bar icon and an iconset for the app icon.
"""

from PIL import Image, ImageDraw
import os

def create_statusbar_icon(size):
    """Create a simple clock icon for the status bar."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    center = size // 2
    radius = int(size * 0.42)
    stroke_width = max(1, size // 12)

    # Draw clock circle
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        outline=(0, 0, 0, 255),
        width=stroke_width
    )

    # Draw hour hand (pointing up)
    hand_length = int(radius * 0.5)
    draw.line(
        [(center, center), (center, center - hand_length)],
        fill=(0, 0, 0, 255),
        width=stroke_width
    )

    # Draw minute hand (pointing right)
    hand_length = int(radius * 0.65)
    draw.line(
        [(center, center), (center + hand_length, center)],
        fill=(0, 0, 0, 255),
        width=stroke_width
    )

    # Draw center dot
    dot_radius = max(1, size // 18)
    draw.ellipse(
        [center - dot_radius, center - dot_radius,
         center + dot_radius, center + dot_radius],
        fill=(0, 0, 0, 255)
    )

    return img

def create_app_icon(size):
    """Create a colorful clock icon for the app."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    center = size // 2
    corner_radius = int(size * 0.22)  # macOS icon corner radius

    # Draw rounded rectangle background with gradient-like effect
    # Top color: #6366f1 (indigo)
    # Bottom color: #8b5cf6 (violet)
    for y in range(size):
        ratio = y / size
        r = int(99 + (139 - 99) * ratio)
        g = int(102 + (92 - 102) * ratio)
        b = int(241 + (246 - 241) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Create rounded corners by drawing over them
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=corner_radius,
        fill=255
    )

    # Apply mask
    img.putalpha(mask)

    # Draw clock face (white circle)
    clock_radius = int(size * 0.33)
    shadow_offset = max(1, size // 128)

    # Shadow
    draw.ellipse(
        [center - clock_radius + shadow_offset,
         center - clock_radius + shadow_offset,
         center + clock_radius + shadow_offset,
         center + clock_radius + shadow_offset],
        fill=(0, 0, 0, 30)
    )

    # Clock face
    draw.ellipse(
        [center - clock_radius, center - clock_radius,
         center + clock_radius, center + clock_radius],
        fill=(255, 255, 255, 242)
    )

    # Draw hour markers
    marker_radius = max(2, size // 64)
    positions = [
        (center, center - clock_radius + marker_radius * 3),  # 12
        (center, center + clock_radius - marker_radius * 3),  # 6
        (center - clock_radius + marker_radius * 3, center),  # 9
        (center + clock_radius - marker_radius * 3, center),  # 3
    ]
    for x, y in positions:
        draw.ellipse(
            [x - marker_radius, y - marker_radius,
             x + marker_radius, y + marker_radius],
            fill=(99, 102, 241, 255)
        )

    # Draw hour hand (pointing up)
    hand_width = max(2, size // 43)
    hand_length = int(clock_radius * 0.55)
    draw.line(
        [(center, center), (center, center - hand_length)],
        fill=(99, 102, 241, 255),
        width=hand_width
    )

    # Draw minute hand (pointing right)
    hand_width = max(2, size // 51)
    hand_length = int(clock_radius * 0.75)
    draw.line(
        [(center, center), (center + hand_length, center)],
        fill=(139, 92, 246, 255),
        width=hand_width
    )

    # Draw center dot
    dot_radius = max(2, size // 37)
    draw.ellipse(
        [center - dot_radius, center - dot_radius,
         center + dot_radius, center + dot_radius],
        fill=(99, 102, 241, 255)
    )

    inner_dot = max(1, size // 64)
    draw.ellipse(
        [center - inner_dot, center - inner_dot,
         center + inner_dot, center + inner_dot],
        fill=(255, 255, 255, 255)
    )

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
