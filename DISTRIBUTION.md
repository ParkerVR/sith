# Work Clock - Distribution Instructions

## For Non-Developers

The **Work Clock.app** in the `dist/` folder is a standalone macOS application that anyone can run without needing Python or any developer tools.

### How to Share

1. **Zip the app:**
   ```bash
   cd dist
   zip -r "Work Clock.zip" "Work Clock.app"
   ```

2. **Share the zip file** via email, cloud storage, or any file sharing method

3. **Recipients can:**
   - Unzip the file
   - Drag "Work Clock.app" to their Applications folder
   - Double-click to run!

### First Run on macOS

When users first open the app, macOS may show a security warning because the app isn't signed. They need to:

1. Right-click (or Control-click) on "Work Clock.app"
2. Select "Open" from the menu
3. Click "Open" in the dialog that appears
4. The app will run and remember this choice for future launches

### What the App Does

- Tracks time spent in allowed applications (configurable via JSON)
- Shows a floating glass HUD with elapsed time
- Displays current app and ACTIVE/IDLE status
- Saves daily summaries and configuration to `~/.workclock/`
- Right-click menu for:
  - Show Work Summary (view time breakdown by app)
  - Quit

### Configuration

The app stores its configuration and data in `~/.workclock/`:

- **config.json** - Application settings (allowlist, colors, window size, etc.)
- **summary.json** - Daily work summaries with per-app time tracking

To customize which apps are tracked, edit `~/.workclock/config.json`:
```json
{
  "allowlist": [
    "Sith",
  ],
  "idle_threshold": 2,
  "colors": {
    "working": "#0077ff",
    "glass_working": "#00d4ff"
  },
  "window": {
    "width": 260,
    "height": 80
  }
}
```

**Note:** You need to restart the app after changing the configuration.

If you delete the config file, the app will recreate it with default settings on next launch.

**Migration:** If you're upgrading from an older version that used `~/.khanh_clock_summary.json`, the app will automatically migrate your summary data to the new location on first launch.

## For Developers

### Building from Source

1. **Setup environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # or: ./venv/bin/activate
   pip install -r requirements.txt
   pip install py2app
   ```

2. **Build the .app:**
   ```bash
   python setup.py py2app
   ```

3. **Find the app:**
   The standalone app will be in `dist/Work Clock.app`

### Clean Build

If you need to rebuild:
```bash
rm -rf build dist
python setup.py py2app
```

### Running in Development

```bash
./venv/bin/python main.py
```

## Technical Details

- **Built with:** Python 3.14, PyObjC, native Cocoa/AppKit
- **Platform:** macOS 10.15+
- **Architecture:** Universal (Apple Silicon + Intel)
- **Size:** ~70MB (includes Python runtime and all dependencies)
- **Process Name:** "Work Clock" (not Python)
- **UI:** Native macOS glass/vibrancy effects

## File Structure

```
Work Clock.app/
├── Contents/
│   ├── Info.plist          # App metadata
│   ├── MacOS/
│   │   └── python          # Python runtime
│   ├── Resources/
│   │   ├── main.py         # Your app code
│   │   ├── settings.py     # Configuration
│   │   ├── utils.py        # Utilities
│   │   └── lib/            # Python libraries
│   └── Frameworks/         # PyObjC frameworks
```

## Troubleshooting

**App won't open:**
- Check System Settings > Privacy & Security
- Look for a message about "Work Clock.app" being blocked
- Click "Open Anyway"

**Timer not counting:**
- Make sure the app you're using is in the allowlist in `~/.workclock/config.json`
- Check that you're not idle (moving mouse/typing)
- The app name shown at the bottom of the HUD must match an entry in the allowlist

**App crashes on close:**
- This is a known issue with some PyObjC builds
- Your data is saved before the crash
- Restarting the app will load your previous session

## License

Personal use only. Modify and distribute as needed.
