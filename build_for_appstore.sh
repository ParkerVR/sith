#!/bin/bash
# Build and sign Sith for Mac App Store submission

set -e  # Exit on error

APP_NAME="Sith"
BUNDLE_ID="com.parkervr.sith"
SIGNING_IDENTITY="3rd Party Mac Developer Application: Parker Van Roy (CWDC2RFBVT)"
INSTALLER_IDENTITY="3rd Party Mac Developer Installer: Parker Van Roy (CWDC2RFBVT)"
ENTITLEMENTS="entitlements.plist"

echo "======================================"
echo "Building $APP_NAME for Mac App Store"
echo "======================================"
echo ""

# Clean previous builds
echo "1. Cleaning previous builds..."
rm -rf build dist
echo "   ✓ Cleaned"
echo ""

# Build with py2app
echo "2. Building app with py2app..."
./venv/bin/python setup.py py2app
if [ $? -ne 0 ]; then
    echo "   ✗ Build failed"
    exit 1
fi
echo "   ✓ Built"
echo ""

# Fix file permissions (must be readable by non-root users)
echo "3. Fixing file permissions..."
chmod -R a+rX "dist/$APP_NAME.app"
echo "   ✓ Permissions fixed"
echo ""

# Sign the app for App Store (sign frameworks first, then main bundle)
echo "4. Signing app for App Store..."

# Sign all frameworks and libraries WITHOUT entitlements
echo "   Signing frameworks and libraries..."
find "dist/$APP_NAME.app/Contents/Frameworks" -name "*.dylib" -o -name "*.so" -o -name "*.framework" 2>/dev/null | while read file; do
    codesign --force --sign "$SIGNING_IDENTITY" --options runtime "$file" 2>/dev/null || true
done

find "dist/$APP_NAME.app/Contents/Resources" -name "*.so" -o -name "*.dylib" 2>/dev/null | while read file; do
    codesign --force --sign "$SIGNING_IDENTITY" --options runtime "$file" 2>/dev/null || true
done

# Sign Python framework if it exists
if [ -d "dist/$APP_NAME.app/Contents/Frameworks/Python.framework" ]; then
    codesign --force --sign "$SIGNING_IDENTITY" --options runtime \
        "dist/$APP_NAME.app/Contents/Frameworks/Python.framework/Versions/Current/Python"
    codesign --force --sign "$SIGNING_IDENTITY" --options runtime \
        "dist/$APP_NAME.app/Contents/Frameworks/Python.framework"
fi

# Sign the Python executable WITH entitlements
if [ -f "dist/$APP_NAME.app/Contents/MacOS/python" ]; then
    echo "   Signing Python executable..."
    codesign --force --sign "$SIGNING_IDENTITY" \
        --entitlements "$ENTITLEMENTS" \
        --options runtime \
        "dist/$APP_NAME.app/Contents/MacOS/python"
fi

# Sign the main app bundle WITH entitlements
echo "   Signing main executable..."
codesign --force --sign "$SIGNING_IDENTITY" \
    --entitlements "$ENTITLEMENTS" \
    --options runtime \
    "dist/$APP_NAME.app"

if [ $? -ne 0 ]; then
    echo "   ✗ Signing failed"
    exit 1
fi
echo "   ✓ Signed"
echo ""

# Verify the signature
echo "5. Verifying signature..."
codesign --verify --deep --strict --verbose=2 "dist/$APP_NAME.app"
if [ $? -ne 0 ]; then
    echo "   ✗ Verification failed"
    exit 1
fi
echo "   ✓ Verified"
echo ""

# Create installer package
echo "6. Creating installer package..."
productbuild --component "dist/$APP_NAME.app" /Applications \
    --sign "$INSTALLER_IDENTITY" \
    "dist/$APP_NAME.pkg"

if [ $? -ne 0 ]; then
    echo "   ✗ Package creation failed"
    exit 1
fi
echo "   ✓ Package created"
echo ""

# Verify the package
echo "7. Verifying package..."
pkgutil --check-signature "dist/$APP_NAME.pkg"
if [ $? -ne 0 ]; then
    echo "   ✗ Package verification failed"
    exit 1
fi
echo "   ✓ Package verified"
echo ""

echo "======================================"
echo "✓ SUCCESS!"
echo "======================================"
echo ""
echo "Your app is ready for App Store submission:"
echo "  dist/$APP_NAME.pkg"
echo ""
echo "Next steps:"
echo "1. Go to https://appstoreconnect.apple.com"
echo "2. Create a new app for macOS"
echo "3. Use Transporter app or altool to upload dist/$APP_NAME.pkg"
echo ""
