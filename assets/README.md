# Assets

This directory contains all the icon and image assets for the Sith time tracking app.

## Source Files (Required)

These are the only files you need to edit:

- **statusbar_icon.svg** - Source SVG for the status bar icon
- **app_icon.svg** - Source SVG for the app icon

## Generated Files (Do Not Edit)

All files in the `./generated/` directory are automatically created by the build script:

### Status Bar Icons
- **generated/statusbar_icon.png** - 18x18px icon for the macOS status bar (1x resolution)
- **generated/statusbar_icon@2x.png** - 36x36px icon for the macOS status bar (2x resolution)

The status bar icons are simple, monochrome clock designs that work as template images. They automatically adapt to light/dark mode.

### App Icons
- **generated/AppIcon.icns** - macOS app icon bundle (all resolutions)
- **generated/AppIcon.iconset/** - Directory containing all individual PNG sizes for the app icon

The app icon features a gradient background (indigo to violet) with a white clock face showing 3:00.

### App Store Assets
- **generated/appstore/app_icon_1024.png** - 1024x1024px app icon for App Store (RGB format, no alpha channel)

Note: Screenshots should be placed manually in `assets/screenshots/` directory.

## Regenerating Icons

After editing the source SVG files, regenerate all icons with:

1. **Install dependencies** (first time only):
   ```bash
   brew install cairo pkg-config
   ./venv/bin/python3.14 -m pip install -r assets/requirements.txt
   ```

2. **Generate icons**:
   ```bash
   ./venv/bin/python3.14 assets/create_icons.py
   ```

The script will automatically:
1. Create the `./generated/` directory structure
2. Generate status bar icons at 1x and 2x resolutions
3. Create all required app icon sizes in the iconset
4. Convert the iconset to .icns format using `iconutil`
5. Generate App Store marketing assets (1024x1024 app icon)

## Design Notes

**Status Bar Icon**: Simple clock design with hands at 3:00 position. Black on transparent background, designed to be used as a template image.

**App Icon**: Colorful gradient background with modern design. Features a white clock face with hour markers at 12, 3, 6, and 9 o'clock positions. Clock hands point to 3:00. Uses indigo and violet colors that match modern macOS design aesthetics.

## Customization

To customize the icons:
1. **Edit the source SVG files** (`statusbar_icon.svg` or `app_icon.svg`)
2. **Modify the `create_icons.py` script** to change colors, gradients, or design elements
3. **Run the generation script** to create updated icons

Make sure to keep the status bar icon simple and legible at small sizes (18x18px).
