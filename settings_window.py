"""
Settings window for the Sith application.
"""

from Cocoa import (
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
    NSNormalWindowLevel,
    NSColor,
    NSColorWell,
    NSPopUpButton,
    NSMakeRect,
    NSFont,
    NSButton,
    NSBezelStyleRounded,
    NSBezelStyleCircular,
    NSScrollView,
    NSView,
)
from Foundation import NSObject, NSTimer
import objc
import json
import subprocess
from display_utils import add_glass_effect, create_label, create_text_field, hex_to_nscolor, nscolor_to_hex, get_font
from utils import load_config, CONFIG_PATH, load_summary, DEFAULT_CONFIG, APP_DIR


class FlippedView(NSView):
    """A view with flipped coordinates (y=0 at top instead of bottom)."""

    def isFlipped(self):
        return True


class SettingsController(NSObject):
    """Controller for the settings window."""

    def init(self):
        self = objc.super(SettingsController, self).init()
        if self is None:
            return None

        self.window = None
        self.scroll_view = None  # Scroll view for content
        self.content_view = None  # Content view inside scroll view
        self.widgets = {}
        self.config = load_config()
        self.on_settings_changed = None  # Callback when settings change
        self.refresh_timer = None  # Timer for refreshing recent apps
        self.last_recent_apps = []  # Track last seen recent apps

        return self

    def createWindow(self):
        """Create and show the settings window."""
        # Create window with close button
        settings_rect = NSMakeRect(100, 100, 380, 500)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            settings_rect,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )

        # Configure window
        self.window.setTitle_("Settings")
        # Use normal window level - settings don't need to float above everything
        self.window.setLevel_(NSNormalWindowLevel)
        # Use system background color with transparency for proper appearance adaptation
        self.window.setBackgroundColor_(NSColor.windowBackgroundColor().colorWithAlphaComponent_(0.95))

        # Accessibility
        self.window.setAccessibilityHelp_("Configure Sith settings including colors, fonts, and tracked applications")

        # Add glass effect
        add_glass_effect(self.window)

        # Create scroll view to hold content
        scroll_rect = self.window.contentView().bounds()
        self.scroll_view = NSScrollView.alloc().initWithFrame_(scroll_rect)
        self.scroll_view.setHasVerticalScroller_(True)
        self.scroll_view.setHasHorizontalScroller_(False)
        self.scroll_view.setAutoresizingMask_(18)  # Width and height resizable
        self.scroll_view.setDrawsBackground_(False)

        # Create content view with estimated height (will be adjusted after building UI)
        allowlist = self.config.get("allowlist", [])
        # Estimate: base (160) + allowlist items (22 each) + buffer (100 for recent apps section)
        estimated_height = 160 + len(allowlist) * 22 + 100
        content_rect = NSMakeRect(0, 0, 380, max(estimated_height, 500))
        self.content_view = FlippedView.alloc().initWithFrame_(content_rect)

        self.scroll_view.setDocumentView_(self.content_view)
        self.window.contentView().addSubview_(self.scroll_view)

        # Build UI
        self.buildUI()

        # Initialize the last_recent_apps list with current state
        recent_apps_all = self.config.get("recent_apps", [])
        allowlist = self.config.get("allowlist", [])
        self.last_recent_apps = [app for app in recent_apps_all if app not in allowlist][:3]

        # Set releasedWhenClosed to False to prevent crashes
        self.window.setReleasedWhenClosed_(False)

        # Set self as delegate to handle window close
        self.window.setDelegate_(self)

        # Start timer to refresh recent apps every 0.5 seconds
        self.refresh_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.5, self, "refreshRecentApps:", None, True
        )

        # Show window
        self.window.makeKeyAndOrderFront_(None)

    def buildUI(self):
        """Build the settings UI."""
        y_position = 20  # Start from top with flipped coordinates

        # Title
        hello_label = create_label("Settings", 20, y_position, 340, 25, bold=True, font_size=18)
        self.content_view.addSubview_(hello_label)

        y_position += 30

        # Info label - changes take effect immediately
        info_label = create_label("Changes take effect immediately.", 20, y_position, 340, 15, bold=False, font_size=10)
        # Use secondary label color for subtle appearance
        info_label.setTextColor_(NSColor.secondaryLabelColor())
        self.content_view.addSubview_(info_label)

        y_position += 25

        # Active color picker
        label = create_label("Active text color:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        active_color_well = NSColorWell.alloc().initWithFrame_(NSMakeRect(180, y_position, 60, 25))
        active_color = hex_to_nscolor(self.config.get("colors", {}).get("glass_working", "#00d4ff"))
        active_color_well.setColor_(active_color)
        active_color_well.setTarget_(self)
        active_color_well.setAction_("activeColorChanged:")
        # Accessibility
        active_color_well.setAccessibilityLabel_("Active text color picker")
        active_color_well.setAccessibilityHelp_("Choose the color displayed when actively tracking work time")
        self.content_view.addSubview_(active_color_well)
        self.widgets['active_color'] = active_color_well

        y_position += 35

        # Idle color picker
        label = create_label("Idle text color:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        idle_color_well = NSColorWell.alloc().initWithFrame_(NSMakeRect(180, y_position, 60, 25))
        idle_color = hex_to_nscolor(self.config.get("colors", {}).get("glass_inactive", "#ffffff"))
        idle_color_well.setColor_(idle_color)
        idle_color_well.setTarget_(self)
        idle_color_well.setAction_("idleColorChanged:")
        # Accessibility
        idle_color_well.setAccessibilityLabel_("Idle text color picker")
        idle_color_well.setAccessibilityHelp_("Choose the color displayed when idle or using non-tracked apps")
        self.content_view.addSubview_(idle_color_well)
        self.widgets['idle_color'] = idle_color_well

        y_position += 50

        # Idle timeout
        label = create_label("Idle timeout:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        idle_field = create_text_field(str(self.config.get("idle_threshold", 2)), 180, y_position, 60, 22)
        idle_field.setTarget_(self)
        idle_field.setAction_("idleTimeoutChanged:")
        # Accessibility
        idle_field.setAccessibilityLabel_("Idle timeout value")
        idle_field.setAccessibilityHelp_("Number of time units before being marked as idle")
        self.content_view.addSubview_(idle_field)
        self.widgets['idle_field'] = idle_field

        # Unit selector dropdown
        unit_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(250, y_position - 2, 90, 26))
        unit_popup.addItemWithTitle_("seconds")
        unit_popup.addItemWithTitle_("minutes")
        unit_popup.addItemWithTitle_("hours")
        unit_popup.selectItemAtIndex_(0)
        unit_popup.setTarget_(self)
        unit_popup.setAction_("idleTimeoutChanged:")
        # Accessibility
        unit_popup.setAccessibilityLabel_("Idle timeout unit")
        unit_popup.setAccessibilityHelp_("Time unit for idle threshold: seconds, minutes, or hours")
        self.content_view.addSubview_(unit_popup)
        self.widgets['unit_popup'] = unit_popup

        y_position += 40

        # Color animation checkbox
        anim_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, y_position, 340, 20))
        anim_checkbox.setButtonType_(3)  # Switch/checkbox type
        anim_checkbox.setTitle_("Enable color fade animation")
        anim_checkbox.setState_(1 if self.config.get("enable_color_animation", True) else 0)
        anim_checkbox.setFont_(get_font("SF Pro", 10, bold=False))
        anim_checkbox.setTarget_(self)
        anim_checkbox.setAction_("colorAnimationChanged:")
        # Accessibility
        anim_checkbox.setAccessibilityHelp_("Smoothly animate color transitions between active and idle states")
        self.content_view.addSubview_(anim_checkbox)
        self.widgets['color_animation'] = anim_checkbox

        y_position += 30

        # Status bar checkbox
        status_bar_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, y_position, 340, 20))
        status_bar_checkbox.setButtonType_(3)  # Switch/checkbox type
        status_bar_checkbox.setTitle_("Show status bar (app name and status)")
        status_bar_checkbox.setState_(1 if self.config.get("show_status_bar", True) else 0)
        status_bar_checkbox.setFont_(get_font("SF Pro", 10, bold=False))
        status_bar_checkbox.setTarget_(self)
        status_bar_checkbox.setAction_("statusBarChanged:")
        # Accessibility
        status_bar_checkbox.setAccessibilityHelp_("Show or hide the app name and IDLE/ACTIVE status at the bottom of the timer window")
        self.content_view.addSubview_(status_bar_checkbox)
        self.widgets['status_bar'] = status_bar_checkbox

        y_position += 30

        # Time display style dropdown
        label = create_label("Time display:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        time_style_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(180, y_position - 2, 160, 26))
        time_style_popup.addItemWithTitle_("HH:MM:SS")
        time_style_popup.addItemWithTitle_("HH:MM")
        time_style_popup.addItemWithTitle_("Human Readable")

        # Select current style
        current_style = self.config.get("time_display_style", "HH:MM:SS")
        style_index = {"HH:MM:SS": 0, "HH:MM": 1, "Human Readable": 2}.get(current_style, 0)
        time_style_popup.selectItemAtIndex_(style_index)

        time_style_popup.setTarget_(self)
        time_style_popup.setAction_("timeStyleChanged:")
        # Accessibility
        time_style_popup.setAccessibilityLabel_("Time display format")
        time_style_popup.setAccessibilityHelp_("Choose how work time is displayed in the timer")
        self.content_view.addSubview_(time_style_popup)
        self.widgets['time_style'] = time_style_popup

        y_position += 40

        # Timer font dropdown
        label = create_label("Timer font:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        font_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(180, y_position - 2, 160, 26))
        font_popup.addItemWithTitle_("SF Pro")
        font_popup.addItemWithTitle_("SF Mono")
        font_popup.addItemWithTitle_("Menlo")

        # Select current font (defaults to Menlo for timer)
        current_font = self.config.get("timer_font_family", "Menlo")
        font_index = {"SF Pro": 0, "SF Mono": 1, "Menlo": 2}.get(current_font, 2)
        font_popup.selectItemAtIndex_(font_index)

        font_popup.setTarget_(self)
        font_popup.setAction_("fontFamilyChanged:")
        # Accessibility
        font_popup.setAccessibilityLabel_("Timer font")
        font_popup.setAccessibilityHelp_("Choose the font style for the timer display only")
        self.content_view.addSubview_(font_popup)
        self.widgets['timer_font_family'] = font_popup

        y_position += 50

        # Allowlist section
        self.allowlist_y_start = y_position
        final_y = self.rebuildAllowlist()

        # Adjust content view height to actual content with some bottom padding
        actual_height = final_y + 40  # 40px bottom padding
        if self.content_view.frame().size.height != actual_height:
            content_rect = NSMakeRect(0, 0, 380, actual_height)
            self.content_view.setFrame_(content_rect)

    def rebuildAllowlist(self):
        """Rebuild the allowlist section (called when list changes).
        Returns the final y position after all elements are added."""
        # Remove all subviews in the allowlist area (we'll rebuild)
        # For simplicity, we'll just rebuild the entire window content
        # In a real app, you'd track and remove specific views

        y_position = self.allowlist_y_start

        label = create_label("App Allowlist:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        y_position += 25

        # Display each app with a remove button
        allowlist = self.config.get("allowlist", [])
        for i, app_name in enumerate(allowlist):
            app_label = create_label(app_name, 30, y_position, 280, 20, font_size=10)
            self.content_view.addSubview_(app_label)

            # Remove button - circular minus
            remove_btn = NSButton.alloc().initWithFrame_(NSMakeRect(315, y_position, 20, 20))
            remove_btn.setTitle_("-")
            remove_btn.setBezelStyle_(NSBezelStyleCircular)  # Circular button style
            remove_btn.setFont_(get_font("SF Pro", 12, bold=False))
            remove_btn.setTag_(i)  # Store index as tag
            remove_btn.setTarget_(self)
            remove_btn.setAction_("removeApp:")
            # Accessibility - hint only, no label (Apple standard for "-" buttons)
            remove_btn.setAccessibilityHelp_(f"Remove {app_name} from allowlist")
            self.content_view.addSubview_(remove_btn)

            y_position += 22

        y_position += 15

        # Add section for recent apps
        add_label = create_label("Add app:", 20, y_position, 150, 20)
        self.content_view.addSubview_(add_label)

        y_position += 30

        # Get recently seen apps from config (not from summary)
        recent_apps_all = self.config.get("recent_apps", [])

        # Filter out apps already in allowlist and take first 3
        recent_apps = [app for app in recent_apps_all if app not in allowlist][:3]

        # Create buttons for recent apps (small size - 28pt height)
        x_pos = 20
        for app_name in recent_apps:
            add_btn = NSButton.alloc().initWithFrame_(NSMakeRect(x_pos, y_position, 100, 28))
            add_btn.setTitle_(app_name)
            add_btn.setBezelStyle_(NSBezelStyleRounded)  # Standard rounded button
            add_btn.setFont_(get_font("SF Pro", 9, bold=False))
            add_btn.setTarget_(self)
            add_btn.setAction_("addApp:")
            # Accessibility
            add_btn.setAccessibilityHelp_(f"Add {app_name} to work tracking allowlist")
            self.content_view.addSubview_(add_btn)
            x_pos += 110

        y_position += 28 + 30  # After buttons + spacing

        # Reset to default button (regular size - 32pt height)
        reset_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, y_position, 340, 32))
        reset_btn.setTitle_("Reset to Default Settings")
        reset_btn.setBezelStyle_(NSBezelStyleRounded)  # Standard rounded button
        reset_btn.setFont_(get_font("SF Pro", 11, bold=False))
        reset_btn.setTarget_(self)
        reset_btn.setAction_("resetToDefault:")
        # Accessibility
        reset_btn.setAccessibilityHelp_("Restore all settings to their default values")
        self.content_view.addSubview_(reset_btn)

        y_position += 32 + 10  # After button + spacing

        # Open app directory button (regular size - 32pt height)
        open_dir_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, y_position, 340, 32))
        open_dir_btn.setTitle_("Open App Directory in Finder")
        open_dir_btn.setBezelStyle_(NSBezelStyleRounded)  # Standard rounded button
        open_dir_btn.setFont_(get_font("SF Pro", 11, bold=False))
        open_dir_btn.setTarget_(self)
        open_dir_btn.setAction_("openAppDirectory:")
        # Accessibility
        open_dir_btn.setAccessibilityHelp_("Open the application data directory in Finder to view configuration files")
        self.content_view.addSubview_(open_dir_btn)

        # Return final y position (after button height)
        return y_position + 32

    @objc.IBAction
    def activeColorChanged_(self, sender):
        """Handle active color picker change."""
        color = sender.color()
        hex_color = nscolor_to_hex(color)

        # Update config
        if "colors" not in self.config:
            self.config["colors"] = {}
        self.config["colors"]["glass_working"] = hex_color

        # Save to file
        self.saveConfig()

    @objc.IBAction
    def idleColorChanged_(self, sender):
        """Handle idle color picker change."""
        color = sender.color()
        hex_color = nscolor_to_hex(color)

        # Update config
        if "colors" not in self.config:
            self.config["colors"] = {}
        self.config["colors"]["glass_inactive"] = hex_color

        # Save to file
        self.saveConfig()

    @objc.IBAction
    def idleTimeoutChanged_(self, sender):
        """Handle idle timeout change."""
        try:
            idle_value = int(self.widgets['idle_field'].stringValue())
            unit_index = self.widgets['unit_popup'].indexOfSelectedItem()

            # Convert to seconds
            multipliers = [1, 60, 3600]  # seconds, minutes, hours
            idle_seconds = idle_value * multipliers[unit_index]

            # Update config
            self.config["idle_threshold"] = idle_seconds

            # Save to file
            self.saveConfig()
        except ValueError:
            pass  # Invalid input, ignore

    @objc.IBAction
    def colorAnimationChanged_(self, sender):
        """Handle color animation checkbox change."""
        enabled = sender.state() == 1
        self.config["enable_color_animation"] = enabled

        # Save to file
        self.saveConfig()

    @objc.IBAction
    def statusBarChanged_(self, sender):
        """Handle status bar checkbox change."""
        enabled = sender.state() == 1
        self.config["show_status_bar"] = enabled

        # Save to file
        self.saveConfig()

    @objc.IBAction
    def timeStyleChanged_(self, sender):
        """Handle time display style dropdown change."""
        styles = ["HH:MM:SS", "HH:MM", "Human Readable"]
        selected_index = sender.indexOfSelectedItem()
        self.config["time_display_style"] = styles[selected_index]

        # Save to file
        self.saveConfig()

    @objc.IBAction
    def fontFamilyChanged_(self, sender):
        """Handle timer font dropdown change."""
        fonts = ["SF Pro", "SF Mono", "Menlo"]
        selected_index = sender.indexOfSelectedItem()
        selected_font = fonts[selected_index]

        self.config["timer_font_family"] = selected_font

        # Save to file
        self.saveConfig()

        # Refresh window to show new font
        self.refreshWindow()

    @objc.IBAction
    def addApp_(self, sender):
        """Handle add app button click."""
        app_name = sender.title()

        # Add to allowlist
        if "allowlist" not in self.config:
            self.config["allowlist"] = []

        if app_name not in self.config["allowlist"]:
            self.config["allowlist"].append(app_name)

            # Save to file
            self.saveConfig()

            # Rebuild UI to show updated list
            self.refreshWindow()

    @objc.IBAction
    def removeApp_(self, sender):
        """Handle remove app button click."""
        index = sender.tag()

        if "allowlist" in self.config and index < len(self.config["allowlist"]):
            self.config["allowlist"].pop(index)

            # Save to file
            self.saveConfig()

            # Rebuild UI to show updated list
            self.refreshWindow()

    @objc.IBAction
    def resetToDefault_(self, sender):
        """Reset all settings to default values."""
        # Reset config to defaults (preserve recent_apps if exists)
        recent_apps = self.config.get("recent_apps", [])
        self.config = DEFAULT_CONFIG.copy()
        self.config["recent_apps"] = recent_apps

        # Save to file
        self.saveConfig()

        # Rebuild UI to show default settings
        self.refreshWindow()

    @objc.IBAction
    def openAppDirectory_(self, sender):
        """Open the app directory in Finder."""
        subprocess.run(['open', str(APP_DIR)])

    def saveConfig(self):
        """Save the configuration to JSON file."""
        CONFIG_PATH.write_text(json.dumps(self.config, indent=2))

        # Notify main app that settings changed
        if self.on_settings_changed:
            self.on_settings_changed()

    def refreshWindow(self):
        """Refresh the window to show updated settings."""
        # Reload config from disk first
        self.config = load_config()

        # Clear the content view
        for view in list(self.content_view.subviews()):
            view.removeFromSuperview()

        # Rebuild UI with fresh config (this will resize content view dynamically)
        self.buildUI()

        # Force window to redisplay
        self.window.display()

    @objc.IBAction
    def refreshRecentApps_(self, timer):
        """Periodically check if recent apps have changed and update UI if needed."""
        # Reload config to get latest recent apps
        config_data = load_config()
        recent_apps_all = config_data.get("recent_apps", [])
        allowlist = config_data.get("allowlist", [])

        # Filter to get the apps that should be displayed
        recent_apps = [app for app in recent_apps_all if app not in allowlist][:3]

        # Check if the list has changed
        if recent_apps != self.last_recent_apps:
            self.last_recent_apps = recent_apps

            # Reload config and refresh window to show new buttons
            self.config = config_data
            self.refreshWindow()

    def windowWillClose_(self, notification):
        """Handle window close - stop the refresh timer."""
        if self.refresh_timer:
            self.refresh_timer.invalidate()
            self.refresh_timer = None


def create_settings_controller():
    """Create and return a settings controller."""
    controller = SettingsController.alloc().init()
    controller.createWindow()
    return controller
