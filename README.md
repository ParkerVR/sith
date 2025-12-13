<div align="center">

<img src="assets/generated/appstore/app_icon_1024.png" width="200" alt="Sith App Icon">

# Sith

**Focus. Track. Achieve.**

*In Archaic English, "Sith" means "journey," "experience," or "point in time."*

A minimal macOS time tracker that helps you understand where your time goes.

[![macOS](https://img.shields.io/badge/macOS-10.15+-blue.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.7+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

</div>

---

## Screenshots

<div align="center">
<img src="assets/screenshots/app.png" width="800" alt="Sith Timer Window">
<br>
<em>Clean, floating timer that stays out of your way</em>
<br><br>
<img src="assets/screenshots/settings.png" width="800" alt="Sith Settings">
<br>
<em>Simple settings to customize your tracking experience</em>
</div>

---

## What Is Sith?

Sith is a minimalist time tracker that quietly sits in the corner of your screen, tracking time spent in the apps you choose. It helps you understand your work patterns without being intrusive.

### Key Features

- **Beautiful Floating Timer** - Minimal, always-on-top display
- **App-Based Tracking** - Only track time in apps you specify
- **Customizable Colors** - Match your workflow and mood
- **Idle Detection** - Automatically pauses when you step away
- **Menu Bar Integration** - Quick access from your status bar
- **Privacy First** - All data stored locally on your Mac
- **Daily Summaries** - Review your time usage patterns

---

## Quick Start

### Prerequisites

- **macOS 10.15+** (Catalina or later)
- **Python 3.7+** installed

### Python Installation

If you don't have Python 3.14+ installed:

```bash
# Install via Homebrew (recommended)
brew install python@3.14

# Or download from python.org
# https://www.python.org/downloads/
```

### Setup & Run

1. **Clone or download this repository**

```bash
cd sith
```

2. **Create virtual environment**

```bash
/opt/homebrew/bin/python3 -m venv venv
```

3. **Install dependencies**

```bash
venv/bin/python3.14 -m pip install -r requirements.txt
```

4. **Run the app (Development)**

```bash
venv/bin/python3.14 main.py
```

The app will launch!

---

## Usage

### First Time Setup

1. **Launch Sith** - The timer appears in the corner of your screen
2. **Right-click the window** - Opens the context menu
3. **Select Settings** - Configure your tracking preferences
4. **Add Apps to Track**:
   - Open the app you want to track (e.g., VS Code, Terminal)
   - It will appear in "Recent Apps" in Settings
   - Click to add it to your allowlist
5. **Start Working** - Sith automatically tracks time in allowed apps!

### Features at a Glance

- **Right-click menu** - Access all features quickly
- **Reset Timer** - Start fresh anytime
- **Work Summary** - View daily time tracking history
- **Settings** - Customize colors, idle timeout, allowed apps
- **Minimize to Status Bar** - Hide window, keep tracking

### Understanding the Display

- **Timer** - Total time tracked today
- **App Name** - Current active application
- **Status** - ACTIVE (tracking) or IDLE (paused)
- **Colors** - Active (working) vs Idle (paused)

---

## Building the App

To create a standalone `.app` bundle:

Install setuptools:
```bash
./venv/bin/python3.14 -m pip install -r dist_requirements.txt
```

```bash
# Clean build
rm -rf build dist

# Build with py2app
./venv/bin/python3.14 setup.py py2app

# Sign the app (required for macOS)
codesign --force --deep --sign - dist/Sith.app

# Create fancy DMG installer for distribution (optional)
./create_dmg.sh

# Run the built app
open dist/Sith.app
```

The app will be in `dist/Sith.app` and can be moved to your Applications folder. For distribution, use `dist/Sith.dmg`.

For detailed build and distribution instructions, see [DISTRIBUTION.md](DISTRIBUTION.md).

---

## Privacy & Data

Sith is **privacy-first**. All your data stays on your Mac:

- **Config:** `~/Library/Application Support/Sith/config.json`
- **History:** `~/Library/Application Support/Sith/summary.json`

No data is sent to any server. No analytics. No tracking. Just local time tracking.

---

## Development

### Dependencies

- **pyobjc-framework-Cocoa** - Native macOS UI
- **pyobjc-framework-Quartz** - Idle time detection
- **setproctitle** - Process name in Activity Monitor
- **markdown** - In-app guide rendering

### Tech Stack

- **Python 3.14** - Core language
- **PyObjC** - Native macOS Cocoa bindings
- **Cocoa/AppKit** - Native macOS UI framework
- **py2app** - macOS app bundling

---

## Documentation

- **[GUIDE.md](GUIDE.md)** - Complete user guide (also available in-app)
- **[DISTRIBUTION.md](DISTRIBUTION.md)** - Building, signing, and distributing
- **[assets/README.md](assets/README.md)** - Icon and asset generation guide

---

## Customization

Edit `config.json` to customize:

```json
{
  "ALLOWLIST": ["Visual Studio Code", "Terminal", "Xcode"],
  "IDLE_THRESHOLD": 60,
  "WORKING_COLOR": "#6366F1",
  "INACTIVE_COLOR": "#6B7280",
  "WINDOW_WIDTH": 180,
  "WINDOW_HEIGHT": 120
}
```

Or use the Settings UI for a more friendly experience!

---

## Troubleshooting

### App won't launch?
```bash
# Re-sign the app
codesign --force --deep --sign - dist/Sith.app
```

### Permission issues?
- Grant Accessibility permissions in System Settings > Privacy & Security
- Required for detecting active applications

### Timer not tracking?
- Make sure your app is in the allowlist (Settings)
- Check that you're not idle (move mouse to reset)

---

## Credit

App is inspired [work.exe](https://neilblr.com/post/58757345346) by Neil Cicierega

work.exe but MacOS and more

---

## License

Copyright © 2025 Parker Van Roy. All rights reserved.

---

<div align="center">

**[Download](dist/)** • **[Documentation](GUIDE.md)** • **[Report Bug](issues/)**

</div>
