#!/bin/bash
# Create a fancy DMG with Applications folder shortcut using create-dmg

set -e

echo "Creating fancy DMG installer..."

# Clean up any existing DMG
rm -f dist/Sith.dmg

# Create DMG with create-dmg tool
create-dmg \
  --volname "Sith" \
  --volicon "assets/generated/AppIcon.icns" \
  --window-pos 200 120 \
  --window-size 500 300 \
  --icon-size 96 \
  --icon "Sith.app" 125 120 \
  --hide-extension "Sith.app" \
  --app-drop-link 375 120 \
  "dist/Sith.dmg" \
  "dist/Sith.app"

echo "✓ DMG created: dist/Sith.dmg"
