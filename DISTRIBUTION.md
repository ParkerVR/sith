# Sith - Distribution Guide

Complete guide for building, signing, and distributing the Sith time tracking app.

---

## Table of Contents

1. [Quick Start for Development](#quick-start-for-development)
2. [Building for Distribution](#building-for-distribution)
3. [Code Signing & Notarization](#code-signing--notarization)
4. [App Store Submission](#app-store-submission)
5. [Direct Distribution (Non-App Store)](#direct-distribution-non-app-store)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start for Development

### Setup Environment
```bash
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m pip install py2app
```

### Run in Development
```bash
./venv/bin/python main.py
```

### Clean Build
```bash
rm -rf build dist
./venv/bin/python setup.py py2app
codesign --force --deep --sign - dist/Sith.app  # Required for app to launch
```

The app will be in `dist/Sith.app`

---

## Building for Distribution

### Prerequisites
- macOS 10.15 or later
- Python 3.7+
- Apple Developer Account ($99/year) for code signing
- Custom app icon (.icns file) - optional but recommended

### Step 1: Prepare Icon (Optional)
If you have a custom icon:
1. Create a 1024x1024 PNG icon
2. Convert to .icns format:
   ```bash
   # Using iconutil
   mkdir MyIcon.iconset
   sips -z 16 16     icon1024.png --out MyIcon.iconset/icon_16x16.png
   sips -z 32 32     icon1024.png --out MyIcon.iconset/icon_16x16@2x.png
   sips -z 32 32     icon1024.png --out MyIcon.iconset/icon_32x32.png
   sips -z 64 64     icon1024.png --out MyIcon.iconset/icon_32x32@2x.png
   sips -z 128 128   icon1024.png --out MyIcon.iconset/icon_128x128.png
   sips -z 256 256   icon1024.png --out MyIcon.iconset/icon_128x128@2x.png
   sips -z 256 256   icon1024.png --out MyIcon.iconset/icon_256x256.png
   sips -z 512 512   icon1024.png --out MyIcon.iconset/icon_256x256@2x.png
   sips -z 512 512   icon1024.png --out MyIcon.iconset/icon_512x512.png
   sips -z 1024 1024 icon1024.png --out MyIcon.iconset/icon_512x512@2x.png
   iconutil -c icns MyIcon.iconset
   ```

3. Update `setup.py`:
   ```python
   'iconfile': 'MyIcon.icns',  # Add your icon here
   ```

### Step 2: Build the App
```bash
# Clean previous builds
rm -rf build dist

# Build
./venv/bin/python setup.py py2app
```

The unsigned app will be in `dist/Sith.app` (~43MB)

### Step 3: Test the Build

**Important:** macOS requires all apps to be code-signed, even for local testing. Add an ad-hoc signature:

```bash
# Add ad-hoc signature for local testing
codesign --force --deep --sign - dist/Sith.app

# Now test the app
dist/Sith.app/Contents/MacOS/Sith
```

Verify:
- ✅ Timer counts up
- ✅ Idle detection works (stop moving mouse for a few seconds)
- ✅ Settings window opens
- ✅ "Open App Directory" button works
- ✅ Data saves to `~/Library/Application Support/Sith/`

---

## Code Signing & Notarization

Required for distribution outside development. Users won't see scary security warnings.

### Prerequisites

1. **Apple Developer Account**
   - Enroll at https://developer.apple.com ($99/year)
   - Note your Team ID (e.g., `CWDC2RFBVT`)

2. **Developer ID Certificate**
   - Go to https://developer.apple.com/account/resources/certificates/list
   - Create **"Developer ID Application"** certificate (NOT "Mac App Distribution")
   - Download and install by double-clicking the .cer file

3. **Verify Certificate Installation**
   ```bash
   security find-identity -v -p codesigning
   ```

   You should see:
   ```
   1) CWDC2RFBVT "Developer ID Application: Parker Van Roy (CWDC2RFBVT)"
   ```

4. **App-Specific Password** (for notarization)
   - Go to https://appleid.apple.com/account/manage
   - Under Security → App-Specific Passwords → Generate
   - Save this password securely

### Step 1: Sign the App

The `sign_app.sh` script is pre-configured with your credentials:

```bash
./sign_app.sh
```

This will:
- Sign all frameworks and dylibs
- Sign the main app with entitlements (sandboxing)
- Enable hardened runtime
- Add secure timestamp
- Verify the signature

**What it does:**
- Enables App Sandbox for security
- Adds entitlements for NSWorkspace access (detecting active app)
- Marks the app as notarization-ready

### Step 2: Notarize with Apple

```bash
./notarize_app.sh YOUR_APPLE_ID_EMAIL
```

Example:
```bash
./notarize_app.sh parker@example.com
```

When prompted:
- Use your **App-Specific Password** (not your regular Apple ID password)

This process takes 2-5 minutes. Apple will:
- Scan your app for malware
- Verify code signature
- Check entitlements
- Approve for distribution

### Step 3: Verify Everything

```bash
# Check signature
codesign -dvvv dist/Sith.app

# Check notarization
spctl -a -vv dist/Sith.app
```

You should see:
- ✅ `Signature=adhoc` → should be your Developer ID
- ✅ `source=Notarized Developer ID`
- ✅ `accepted`

### Troubleshooting Signing/Notarization

**"No identity found"**
- Install your Developer ID certificate from Apple Developer portal
- Verify with `security find-identity -v -p codesigning`

**"Invalid password"**
- Use App-Specific Password, not regular Apple ID password
- Generate at https://appleid.apple.com/account/manage

**Notarization rejected**
- Check email for rejection details
- Common issues: missing entitlements, hardened runtime not enabled
- Re-run `./sign_app.sh` to fix

**"The executable does not have the hardened runtime enabled"**
- The sign script already includes `--options runtime`
- Make sure you're running the latest `sign_app.sh`

---

## App Store Submission

For Mac App Store distribution (optional - more restrictive than direct distribution).

### Additional Requirements

1. **Mac App Store Certificate** (different from Developer ID)
   - Go to https://developer.apple.com/account/resources/certificates/list
   - Create **"Mac App Distribution"** certificate
   - Download and install

2. **App Store Connect**
   - Create app listing at https://appstoreconnect.apple.com
   - Bundle ID: `com.parkervanroy.sith`
   - Category: Productivity

3. **Marketing Assets** (✅ Already created in `assets/appstore/`)
   - **App Icon:** `app_icon_1024.png` (1024x1024, no rounded corners)
   - **Screenshots:** Multiple sizes provided (1280x800 up to 2880x1800)
     - Main timer window
     - Settings interface
   - **Hero Image:** For website/marketing use
   - See `assets/appstore/README.md` for complete asset guide

### Submission Process

1. **Build for App Store**
   ```bash
   # Use productbuild for App Store
   # TODO: Add App Store specific build commands
   ```

2. **Upload via Xcode or Transporter**
   - Use Transporter app (download from App Store)
   - Or use Xcode's Organizer

3. **Submit for Review**
   - Fill out all metadata in App Store Connect
   - Add privacy policy if required
   - Submit for review (typically 1-3 days)

### App Store Metadata Template

**App Name:** Sith

**Subtitle:** Work Time Tracker

**Description:**
```
Sith is a minimalist work time tracker that helps you stay focused and understand where your time goes.

Features:
• Beautiful floating timer with glass effect
• Automatic idle detection
• Track time by application
• Daily and historical summaries
• Customizable appearance
• Native macOS design

Sith quietly sits in your menu bar, tracking time spent in your chosen applications. Perfect for freelancers, remote workers, and anyone who wants to understand their productivity patterns.
```

**Keywords:** time tracker, productivity, timer, work, focus, timesheet

**Support URL:** [Your support page/GitHub]

**Privacy Policy:** Required if collecting any data

---

## Direct Distribution (Non-App Store)

Simpler distribution without App Store restrictions.

### Step 1: Sign & Notarize
Follow [Code Signing & Notarization](#code-signing--notarization) section above.

### Step 2: Create Distribution Package

```bash
cd dist
zip -r Sith.zip Sith.app
```

### Step 3: Distribute
- Upload to your website
- Share via cloud storage (Dropbox, Google Drive, etc.)
- Distribute via email
- Host on GitHub releases

### User Installation (Direct Distribution)

1. **Download and unzip** Sith.zip
2. **Move to Applications:**
   - Drag Sith.app to /Applications folder
3. **First launch:**
   - Double-click Sith.app
   - Grant permissions when prompted (detecting active app)
4. **Configure:**
   - Right-click timer → Settings
   - Add applications to track in allowlist

**No security warnings** if properly signed and notarized!

---

## Configuration

### App Data Location
```
~/Library/Application Support/Sith/
├── config.json      # App settings
└── summary.json     # Time tracking data
```

### config.json Structure
```json
{
  "allowlist": [
    "Sith",
    "Xcode",
    "VS Code"
  ],
  "idle_threshold": 2,
  "enable_color_animation": true,
  "show_status_bar": true,
  "time_display_style": "HH:MM:SS",
  "timer_font_family": "Menlo",
  "colors": {
    "working": "#0077ff",
    "inactive": "#aa0000",
    "text": "#ffffff",
    "glass_working": "#00d4ff",
    "glass_inactive": "#ffffff"
  },
  "window": {
    "opacity": 0.9,
    "width": 260,
    "height": 80,
    "margin_x": 20,
    "margin_y": 60
  },
  "update_interval": 1000
}
```

### Migration from Old Versions
The app automatically migrates data from `~/.sith/` to the new location on first launch.

---

## Troubleshooting

### Build Issues

**"ModuleNotFoundError: No module named 'setuptools'"**
```bash
./venv/bin/pip install setuptools py2app
```

**"pyobjc-framework-Quartz not found"**
```bash
./venv/bin/pip install pyobjc-framework-Quartz
```

**Build succeeds but app won't launch**
```bash
# Check for errors
dist/Sith.app/Contents/MacOS/Sith

# Look at crash logs
open ~/Library/Logs/DiagnosticReports/
```

### Runtime Issues

**Timer not counting**
- Check allowlist in Settings
- Current app name (shown at bottom) must match allowlist entry
- Make sure you're not idle

**Idle detection not working**
- Move mouse or type - should switch from IDLE to ACTIVE
- Check `idle_threshold` in config (default 2 seconds)

**Permission denied for detecting active app**
- Grant Accessibility permission:
  - System Settings → Privacy & Security → Accessibility
  - Add Sith to the list

**Data not saving**
- Check `~/Library/Application Support/Sith/` exists
- Check file permissions
- Check Console.app for error messages

**App crashes on quit**
- Known issue with some PyObjC builds
- Data is saved before crash
- Safe to ignore

### Distribution Issues

**"App is damaged and can't be opened"**
- App needs to be signed and notarized
- Or: Users need to right-click → Open (first launch only)

**Gatekeeper blocks the app**
- Sign with Developer ID certificate
- Notarize with Apple
- Verify: `spctl -a -vv dist/Sith.app`

**Users see security warning**
- App is not notarized
- Follow [Code Signing & Notarization](#code-signing--notarization) section

---

## Technical Details

- **Built with:** Python 3.14, PyObjC, native Cocoa/AppKit
- **Platform:** macOS 10.15+
- **Architecture:** ARM64 (Apple Silicon) - can build Universal Binary
- **Size:** ~43MB (includes Python runtime and dependencies)
- **Sandbox:** Yes (required for App Store)
- **Hardened Runtime:** Yes (required for notarization)
- **UI Framework:** Native macOS (NSWindow, NSVisualEffectView)
- **Idle Detection:** Quartz.CGEventSource (sandbox-compatible)
- **App Detection:** NSWorkspace (requires entitlements)

### File Structure
```
Sith.app/
├── Contents/
│   ├── Info.plist                    # App metadata, privacy strings
│   ├── MacOS/
│   │   └── Sith                      # Python runtime + app code
│   ├── Resources/
│   │   ├── lib/python3.14/           # Python standard library
│   │   ├── main.py                   # Main application
│   │   ├── utils.py                  # Utility functions
│   │   ├── settings_window.py        # Settings UI
│   │   ├── summary_window.py         # Summary UI
│   │   └── display_utils.py          # Display helpers
│   ├── Frameworks/                   # PyObjC frameworks
│   └── _CodeSignature/               # Code signature data
```

### Bundle Information
- **Bundle ID:** `com.parkervanroy.sith`
- **Version:** 1.0.0
- **Category:** Productivity
- **Copyright:** Copyright © 2025 Parker Van Roy. All rights reserved.
- **Min macOS:** 10.15.0

### Privacy & Permissions
- **NSAppleEventsUsageDescription:** "Sith needs to know which app you're using to track your work time accurately."
- **Entitlements:**
  - `com.apple.security.app-sandbox` - App Sandbox
  - `com.apple.security.automation.apple-events` - Detect active app

---

## Maintenance Checklist

### Before Each Release
- [ ] Update version in `setup.py` (`CFBundleVersion` and `CFBundleShortVersionString`)
- [ ] Test clean build from scratch
- [ ] Verify all features work
- [ ] Update copyright year if needed
- [ ] Add custom icon if available
- [ ] Update CHANGELOG or release notes

### Build Process
- [ ] Clean build: `rm -rf build dist && ./venv/bin/python setup.py py2app`
- [ ] Test unsigned app
- [ ] Sign: `./sign_app.sh`
- [ ] Notarize: `./notarize_app.sh YOUR_EMAIL`
- [ ] Verify: `spctl -a -vv dist/Sith.app`
- [ ] Test signed app
- [ ] Create distribution zip

### Distribution
- [ ] Upload to hosting
- [ ] Update download links
- [ ] Announce release
- [ ] Monitor for user issues

---

## License

Copyright © 2025 Parker Van Roy. All rights reserved.

For personal and commercial use. Modify and distribute as needed.

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review Console.app logs
- Check `~/Library/Logs/DiagnosticReports/` for crash logs

---

**Last Updated:** December 2025
**App Version:** 1.0.0
**Build System:** py2app 0.28.9
**Python Version:** 3.14
