# App Store Assets

Professional marketing and distribution assets for the Sith time tracking app.

## Generated Assets

### App Icon
- **app_icon_1024.png** (1024x1024) - Required for Mac App Store submission
  - High-resolution app icon
  - Must NOT have rounded corners (App Store adds them)
  - Used in App Store listing

### Screenshots

macOS App Store requires screenshots in at least one of these sizes:

#### Timer Window Screenshots
- **screenshot_2880x1800.png** - For Retina 5K displays
- **screenshot_2560x1600.png** - For Retina displays
- **screenshot_1440x900.png** - Standard MacBook Pro
- **screenshot_1280x800.png** - Standard MacBook Air

All show the main timer window with:
- macOS-style window chrome (traffic lights, title bar)
- Timer display showing "2:45:30"
- "Working" status indicator
- Beautiful gradient background

#### Settings Window Screenshot
- **screenshot_settings_2560x1600.png** - Shows the settings interface
  - Allowed apps list
  - Configuration options
  - Color settings

### Marketing/Promotional

- **hero_2560x1440.png** - Hero image for website/marketing
  - Large app icon
  - "Sith" title
  - "Focus. Track. Achieve." tagline
  - Gradient brand background

- **preview_1200x675.png** - Smaller preview for web/social media
  - Same design as hero, web-optimized size
  - Good for Twitter/LinkedIn posts

## App Store Submission Requirements

### Screenshot Requirements (macOS)

**Minimum:** You must provide at least one screenshot size from:
- 1280 x 800 pixels
- 1440 x 900 pixels
- 2560 x 1600 pixels
- 2880 x 1800 pixels

**Recommended:** Provide all sizes for best presentation across devices.

**Format:**
- PNG or JPEG
- RGB color space
- No alpha channel in final submission

**Quantity:**
- Minimum: 1 screenshot
- Maximum: 10 screenshots
- Recommended: 3-5 showing key features

### App Icon Requirements

- **Size:** 1024 x 1024 pixels
- **Format:** PNG (no transparency)
- **Color:** RGB (not grayscale)
- **Shape:** Square (no rounded corners - Apple adds them)
- **Content:** Must match your app icon exactly

## Usage Guide

### For App Store Connect

1. **Log into App Store Connect**
2. **Create new app or select existing**
3. **Navigate to App Information:**
   - Upload `app_icon_1024.png` as the App Icon

4. **Navigate to macOS App section:**
   - Under "App Previews and Screenshots"
   - Upload screenshots for your target display size
   - Add descriptive captions for each screenshot

5. **Recommended Upload Order:**
   - Main timer window (screenshot_2560x1600.png)
   - Settings window (screenshot_settings_2560x1600.png)
   - Status bar integration (if you create one)

### For Marketing

- Use `hero_2560x1440.png` for website hero sections
- Use `preview_1200x675.png` for social media posts
- Screenshots can be used in blog posts, documentation

## Regenerating Assets

To regenerate all assets:

```bash
cd assets/appstore
../../venv/bin/python3 create_appstore_assets.py
```

The script will recreate all marketing assets with current branding.

## Customization

Edit `create_appstore_assets.py` to customize:
- **Colors:** Change gradient values in hero/screenshot functions
- **Content:** Modify the timer display, status text
- **Layout:** Adjust window positions, sizes
- **Text:** Update tagline, feature descriptions

## App Store Listing Tips

### Title
Keep it short and descriptive: "Sith - Time Tracker" or "Sith: Focus Time Tracking"

### Subtitle (30 characters max)
Examples:
- "Track your productive time"
- "Focus time tracking for Mac"

### Description
Focus on benefits:
- ✓ Beautiful floating timer window
- ✓ Track time in allowed apps
- ✓ Menu bar integration
- ✓ Clean, minimal interface
- ✓ Privacy-focused (local data only)

### Keywords
Separate with commas (100 chars max):
"time tracking,productivity,timer,focus,work timer,time management,task tracking"

### Categories
- **Primary:** Productivity
- **Secondary:** Business or Developer Tools

## Design Notes

All assets use the Sith brand colors:
- **Primary:** Indigo (#6366F1 / RGB 99, 102, 241)
- **Secondary:** Violet (#8B5CF6 / RGB 139, 92, 246)
- **Accent:** White for text and UI elements

Window mockups follow macOS Big Sur+ design guidelines with:
- 10px corner radius
- Traffic light buttons (red, yellow, green)
- Proper title bar styling
- Subtle shadows
