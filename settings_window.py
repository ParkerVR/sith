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
)
from Foundation import NSObject
import objc
import json
from display_utils import add_glass_effect, create_label, create_text_field, hex_to_nscolor, nscolor_to_hex
from utils import load_config, CONFIG_PATH, load_summary


class SettingsController(NSObject):
    """Controller for the settings window."""

    def init(self):
        self = objc.super(SettingsController, self).init()
        if self is None:
            return None

        self.window = None
        self.widgets = {}
        self.config = load_config()
        self.on_settings_changed = None  # Callback when settings change

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

        # Build UI
        self.buildUI()

        # Set releasedWhenClosed to False to prevent crashes
        self.window.setReleasedWhenClosed_(False)

        # Show window
        self.window.makeKeyAndOrderFront_(None)

    def buildUI(self):
        """Build the settings UI."""
        y_position = 450

        # Title
        hello_label = create_label("Settings", 20, y_position, 340, 25, bold=True, font_size=18)
        self.window.contentView().addSubview_(hello_label)

        y_position -= 40

        # Color picker
        label = create_label("Active text color:", 20, y_position, 150, 20)
        self.window.contentView().addSubview_(label)

        color_well = NSColorWell.alloc().initWithFrame_(NSMakeRect(180, y_position, 60, 25))
        active_color = hex_to_nscolor(self.config.get("colors", {}).get("glass_working", "#00d4ff"))
        color_well.setColor_(active_color)
        color_well.setTarget_(self)
        color_well.setAction_("colorChanged:")
        self.window.contentView().addSubview_(color_well)
        self.widgets['active_color'] = color_well

        y_position -= 50

        # Idle timeout
        label = create_label("Idle timeout:", 20, y_position, 150, 20)
        self.window.contentView().addSubview_(label)

        idle_field = create_text_field(str(self.config.get("idle_threshold", 2)), 180, y_position, 60, 22)
        idle_field.setTarget_(self)
        idle_field.setAction_("idleTimeoutChanged:")
        self.window.contentView().addSubview_(idle_field)
        self.widgets['idle_field'] = idle_field

        # Unit selector dropdown
        unit_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(250, y_position - 2, 90, 26))
        unit_popup.addItemWithTitle_("seconds")
        unit_popup.addItemWithTitle_("minutes")
        unit_popup.addItemWithTitle_("hours")
        unit_popup.selectItemAtIndex_(0)
        unit_popup.setTarget_(self)
        unit_popup.setAction_("idleTimeoutChanged:")
        self.window.contentView().addSubview_(unit_popup)
        self.widgets['unit_popup'] = unit_popup

        y_position -= 50

        # Allowlist section
        self.allowlist_y_start = y_position
        self.rebuildAllowlist()

    def rebuildAllowlist(self):
        """Rebuild the allowlist section (called when list changes)."""
        # Remove all subviews in the allowlist area (we'll rebuild)
        # For simplicity, we'll just rebuild the entire window content
        # In a real app, you'd track and remove specific views

        y_position = self.allowlist_y_start

        label = create_label("App Allowlist:", 20, y_position, 150, 20)
        self.window.contentView().addSubview_(label)

        y_position -= 25

        # Display each app with a remove button
        allowlist = self.config.get("allowlist", [])
        for i, app_name in enumerate(allowlist):
            app_label = create_label(app_name, 30, y_position, 280, 20, font_size=10)
            self.window.contentView().addSubview_(app_label)

            # Remove button - circular minus
            remove_btn = NSButton.alloc().initWithFrame_(NSMakeRect(315, y_position, 20, 20))
            remove_btn.setTitle_("-")
            remove_btn.setBezelStyle_(4)
            remove_btn.setFont_(NSFont.fontWithName_size_("Menlo", 12))
            remove_btn.setTag_(i)  # Store index as tag
            remove_btn.setTarget_(self)
            remove_btn.setAction_("removeApp:")
            self.window.contentView().addSubview_(remove_btn)

            y_position -= 22

        y_position -= 15

        # Add section for recent apps
        add_label = create_label("Add app:", 20, y_position, 150, 20)
        self.window.contentView().addSubview_(add_label)

        y_position -= 30

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
            self.window.contentView().addSubview_(add_btn)
            x_pos += 110

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
        print(f"Active color changed to: {hex_color}")

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
            print(f"Idle timeout changed to: {idle_seconds} seconds")
        except ValueError:
            print("Invalid idle timeout value")

    @objc.IBAction
    def addApp_(self, sender):
        """Handle add app button click."""
        print(f"addApp_ called! sender={sender}")
        app_name = sender.title()
        print(f"Adding app: {app_name}")

        # Add to allowlist
        if "allowlist" not in self.config:
            self.config["allowlist"] = []

        if app_name not in self.config["allowlist"]:
            self.config["allowlist"].append(app_name)
            print(f"App added to config, now: {self.config['allowlist']}")

            # Save to file
            print("BEFORE saveConfig()")
            self.saveConfig()
            print("AFTER saveConfig() - about to refresh")

            # Rebuild UI to show updated list
            self.refreshWindow()
        else:
            print(f"App {app_name} already in allowlist")

    @objc.IBAction
    def removeApp_(self, sender):
        """Handle remove app button click."""
        print(f"removeApp_ called! sender={sender}")
        index = sender.tag()
        print(f"Button tag (index): {index}")

        if "allowlist" in self.config and index < len(self.config["allowlist"]):
            app_name = self.config["allowlist"][index]
            print(f"Removing app at index {index}: {app_name}")
            self.config["allowlist"].pop(index)
            print(f"Allowlist after removal: {self.config['allowlist']}")

            # Save to file
            self.saveConfig()
            print(f"Saved config after removing: {app_name}")

            # Rebuild UI to show updated list
            print("About to refresh window...")
            self.refreshWindow()
        else:
            print(f"Invalid index {index} or no allowlist in config")

    def saveConfig(self):
        """Save the configuration to JSON file."""
        CONFIG_PATH.write_text(json.dumps(self.config, indent=2))
        print(f"Config saved to {CONFIG_PATH}")

        # Notify main app that settings changed
        print(f"About to call callback, on_settings_changed={self.on_settings_changed}")
        if self.on_settings_changed:
            print("Calling on_settings_changed callback...")
            self.on_settings_changed()
            print("Callback completed, returning from saveConfig")

    def refreshWindow(self):
        """Refresh the window to show updated settings."""
        # Reload config from disk first
        self.config = load_config()
        print(f"Refreshing window with allowlist: {self.config.get('allowlist', [])}")

        # Clear and rebuild the window content
        for view in list(self.window.contentView().subviews()):
            view.removeFromSuperview()

        # Add glass effect back
        add_glass_effect(self.window)

        # Rebuild UI with fresh config
        self.buildUI()

        # Force window to redisplay
        self.window.display()
        print("Window refreshed and displayed")


def create_settings_controller():
    """Create and return a settings controller."""
    controller = SettingsController.alloc().init()
    controller.createWindow()
    return controller
