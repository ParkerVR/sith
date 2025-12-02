#!/bin/bash
# Script to notarize the app with Apple
# Usage: ./notarize_app.sh YOUR_APPLE_ID_EMAIL

set -e

if [ -z "$1" ]; then
    echo "Usage: ./notarize_app.sh YOUR_APPLE_ID_EMAIL"
    echo "Example: ./notarize_app.sh parker@example.com"
    exit 1
fi

APPLE_ID="$1"
TEAM_ID="CWDC2RFBVT"
APP_PATH="dist/Sith.app"
ZIP_PATH="dist/Sith.zip"

echo "Creating zip for notarization..."
ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"

echo "Submitting to Apple for notarization..."
echo "This may take a few minutes..."
xcrun notarytool submit "$ZIP_PATH" \
    --apple-id "$APPLE_ID" \
    --team-id "$TEAM_ID" \
    --wait

echo "Stapling notarization ticket to app..."
xcrun stapler staple "$APP_PATH"

echo "Verifying stapled app..."
spctl -a -vv "$APP_PATH"

echo ""
echo "✅ Done! Your app is now signed and notarized."
echo "   - Signed with hardened runtime"
echo "   - Notarized by Apple"
echo "   - Ready for distribution"
