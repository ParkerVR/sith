"""
Settings window for the Work Clock application.
"""

from Cocoa import (
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
    NSColor,
    NSColorWell,
    NSPopUpButton,
    NSMakeRect,
    NSFont,
    NSButton,
    NSScrollView,
    NSView,
)
from Foundation import NSObject, NSTimer
import objc
import json
from display_utils import add_glass_effect, create_label, create_text_field, hex_to_nscolor, nscolor_to_hex
from utils import load_config, CONFIG_PATH, load_summary


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
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.95))

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

        y_position += 40

        # Color picker
        label = create_label("Active text color:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        color_well = NSColorWell.alloc().initWithFrame_(NSMakeRect(180, y_position, 60, 25))
        active_color = hex_to_nscolor(self.config.get("colors", {}).get("glass_working", "#00d4ff"))
        color_well.setColor_(active_color)
        color_well.setTarget_(self)
        color_well.setAction_("colorChanged:")
        self.content_view.addSubview_(color_well)
        self.widgets['active_color'] = color_well

        y_position += 50

        # Idle timeout
        label = create_label("Idle timeout:", 20, y_position, 150, 20)
        self.content_view.addSubview_(label)

        idle_field = create_text_field(str(self.config.get("idle_threshold", 2)), 180, y_position, 60, 22)
        idle_field.setTarget_(self)
        idle_field.setAction_("idleTimeoutChanged:")
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
        self.content_view.addSubview_(unit_popup)
        self.widgets['unit_popup'] = unit_popup

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
            remove_btn.setBezelStyle_(4)
            remove_btn.setFont_(NSFont.fontWithName_size_("Menlo", 12))
            remove_btn.setTag_(i)  # Store index as tag
            remove_btn.setTarget_(self)
            remove_btn.setAction_("removeApp:")
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

        # Create buttons for recent apps
        x_pos = 20
        for app_name in recent_apps:
            add_btn = NSButton.alloc().initWithFrame_(NSMakeRect(x_pos, y_position, 100, 28))
            add_btn.setTitle_(app_name)
            add_btn.setBezelStyle_(1)
            add_btn.setFont_(NSFont.fontWithName_size_("Menlo", 9))
            add_btn.setTarget_(self)
            add_btn.setAction_("addApp:")
            self.content_view.addSubview_(add_btn)
            x_pos += 110

        # Return final y position (after button height)
        return y_position + 28

    @objc.IBAction
    def colorChanged_(self, sender):
        """Handle color picker change."""
        color = sender.color()
        hex_color = nscolor_to_hex(color)

        # Update config
        if "colors" not in self.config:
            self.config["colors"] = {}
        self.config["colors"]["glass_working"] = hex_color

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
