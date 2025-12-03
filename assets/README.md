# Assets

This directory contains all the icon and image assets for the Sith time tracking app.

## Files

### Status Bar Icon
- **statusbar_icon.png** - 18x18px icon for the macOS status bar (1x resolution)
- **statusbar_icon@2x.png** - 36x36px icon for the macOS status bar (2x resolution)
- **statusbar_icon.svg** - Source SVG for the status bar icon

The status bar icons are simple, monochrome clock designs that work as template images. They automatically adapt to light/dark mode.

### App Icon
- **AppIcon.icns** - macOS app icon bundle (all resolutions)
- **AppIcon.iconset/** - Directory containing all individual PNG sizes for the app icon
- **app_icon.svg** - Source SVG for the app icon

The app icon features a gradient background (indigo to violet) with a white clock face showing 3:00.

### Regenerating Icons
Install requirements
```
./venv/bin/python -m pip install -r assets/requirements.txt
```
 
Generate icons from SVG:

```
./venv/bin/python assets/create_icons.py
``` 
to regenerate all icon files from the source code.

The script will:
1. Create status bar icons at 1x and 2x resolutions
2. Generate all required app icon sizes in the iconset
3. Convert the iconset to .icns format using `iconutil`

## Design Notes

**Status Bar Icon**: Simple clock design with hands at 3:00 position. Black on transparent background, designed to be used as a template image.

**App Icon**: Colorful gradient background with modern design. Features a white clock face with hour markers at 12, 3, 6, and 9 o'clock positions. Clock hands point to 3:00. Uses indigo and violet colors that match modern macOS design aesthetics.

## Customization

To customize the icons, you can either:
1. Edit the SVG files directly
2. Modify the `create_icons.py` script to change colors, sizes, or design elements
3. Replace the PNG/ICNS files with your own designs

Make sure to keep the status bar icon simple and legible at small sizes (18x18px).
