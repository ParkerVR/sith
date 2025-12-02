#!/bin/bash
# Script to sign the app with entitlements for sandboxing
# Usage: ./sign_app.sh

APP_PATH="dist/Sith.app"
ENTITLEMENTS="entitlements.plist"
IDENTITY="Developer ID Application: YOUR NAME (TEAMID)"

echo "Signing $APP_PATH with entitlements..."

# Sign all frameworks first
find "$APP_PATH/Contents/Frameworks" -name "*.dylib" -o -name "*.framework" | while read framework; do
    echo "Signing: $framework"
    codesign --force --sign "$IDENTITY" --timestamp "$framework"
done

# Sign the main app with entitlements
codesign --deep --force --sign "$IDENTITY" \
    --entitlements "$ENTITLEMENTS" \
    --options runtime \
    --timestamp \
    "$APP_PATH"

echo "Verifying signature..."
codesign -dvvv "$APP_PATH"
codesign --verify --verbose=4 "$APP_PATH"

echo "Done! App is signed with sandbox entitlements."
