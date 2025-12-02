"""
Sith - Main application window and entry point.
Tracks time spent in allowed applications and displays it in a floating window.
Uses native Cocoa/PyObjC for proper glass effect integration.
"""

from Cocoa import (
    NSApplication,
    NSWindow,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
    NSTextField,
    NSColor,
    NSFont,
    NSVisualEffectView,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialHUDWindow,
    NSMenu,
    NSMenuItem,
    NSTimer,
    NSMakeRect,
    NSRightMouseDown,
    NSLeftMouseDown,
    NSLeftMouseDragged,
    NSApp,
    NSApplicationActivationPolicyAccessory,
    NSScreen,
    NSButton,
    NSBezelStyleRounded,
    NSTextAlignmentCenter,
    NSTextView,
    NSScrollView,
    NSMakeSize,
    NSColorWell,
    NSSlider,
    NSTableView,
    NSTableColumn,
    NSBezelBorder,
    NSPopUpButton,
)
from Foundation import NSObject, NSMutableArray, NSProcessInfo
import objc
import setproctitle
import json

from utils import (
    get_frontmost_app_name,
    get_idle_seconds,
    format_seconds,
    load_summary,
    save_summary,
    today_key,
    human_date,
    get_config,
    load_config,
    CONFIG_PATH,
)
from display_utils import hex_to_nscolor, nscolor_to_hex
from summary_window import create_summary_window
from settings_window import create_settings_controller

# Load configuration from JSON
config = get_config()
ALLOWLIST = config.ALLOWLIST
IDLE_THRESHOLD = config.IDLE_THRESHOLD
WORKING_COLOR = config.WORKING_COLOR
INACTIVE_COLOR = config.INACTIVE_COLOR
TEXT_COLOR = config.TEXT_COLOR
GLASS_WORKING_COLOR = config.GLASS_WORKING_COLOR
GLASS_INACTIVE_COLOR = config.GLASS_INACTIVE_COLOR
WINDOW_WIDTH = config.WINDOW_WIDTH
WINDOW_HEIGHT = config.WINDOW_HEIGHT
WINDOW_MARGIN_X = config.WINDOW_MARGIN_X
WINDOW_MARGIN_Y = config.WINDOW_MARGIN_Y
UPDATE_INTERVAL = config.UPDATE_INTERVAL


class SithWindow(NSObject):
    """Main Sith window using native Cocoa."""

    def init(self):
        self = objc.super(SithWindow, self).init()
        if self is None:
            return None

        # Timer + summary state
        self.worked_seconds = 0
        self.is_working = False
        self.current_app = None
        self.summary = load_summary()
        self.today = today_key()

        # Drag state
        self.drag_offset = None

        # Keep references to summary windows to prevent deallocation
        self.summary_windows = []

        # Initialize today's entry if needed
        if self.today not in self.summary:
            self.summary[self.today] = {"total": 0, "by_app": {}}

        # Create window
        self.create_window()

        # Start update timer
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            UPDATE_INTERVAL / 1000.0,  # Convert ms to seconds
            self,
            "updateTimer:",
            None,
            True,
        )

        return self

    def create_window(self):
        """Create the main window with glass effect."""
        # Calculate window position (bottom-right)
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        x = screen_frame.size.width - WINDOW_WIDTH - WINDOW_MARGIN_X
        y = WINDOW_MARGIN_Y

        window_rect = NSMakeRect(x, y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Create borderless window
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )

        # Configure window
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setMovableByWindowBackground_(True)

        # Add glass effect view
        effect_view = NSVisualEffectView.alloc().initWithFrame_(
            self.window.contentView().bounds()
        )
        effect_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
        effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        effect_view.setState_(1)  # Active
        effect_view.setAutoresizingMask_(18)  # Flexible width and height

        self.window.contentView().addSubview_(effect_view)

        # Create text fields
        self.create_labels()

        # Create context menu
        self.create_menu()

        # Set window delegate for handling events
        self.window.setDelegate_(self)

        # Show window
        self.window.makeKeyAndOrderFront_(None)

    def create_menu(self):
        """Create right-click context menu."""
        self.menu = NSMenu.alloc().init()

        # Show Summary menu item
        summary_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show Work Summary", "showSummary:", ""
        )
        summary_item.setTarget_(self)
        self.menu.addItem_(summary_item)

        # Settings menu item
        settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings", "showSettings:", ""
        )
        settings_item.setTarget_(self)
        self.menu.addItem_(settings_item)

        # Guide menu item
        guide_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Guide", "showGuide:", ""
        )
        guide_item.setTarget_(self)
        self.menu.addItem_(guide_item)

        # Reset Timer menu item
        reset_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Reset Timer", "resetTimer:", ""
        )
        reset_item.setTarget_(self)
        self.menu.addItem_(reset_item)

        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())

        # Quit menu item
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", "q"
        )
        quit_item.setTarget_(self)
        self.menu.addItem_(quit_item)

        # Enable right-click on content view
        self.window.contentView().setMenu_(self.menu)

    def create_labels(self):
        """Create text labels for timer, app name, and status."""
        content_view = self.window.contentView()

        # Timer label (large, centered)
        timer_rect = NSMakeRect(0, 25, WINDOW_WIDTH, 35)
        self.timer_label = NSTextField.alloc().initWithFrame_(timer_rect)
        self.timer_label.setStringValue_("00:00:00")
        self.timer_label.setFont_(NSFont.fontWithName_size_("Menlo Bold", 20))
        self.timer_label.setTextColor_(NSColor.whiteColor())
        self.timer_label.setBackgroundColor_(NSColor.clearColor())
        self.timer_label.setBezeled_(False)
        self.timer_label.setDrawsBackground_(False)
        self.timer_label.setEditable_(False)
        self.timer_label.setSelectable_(False)
        self.timer_label.setAlignment_(NSTextAlignmentCenter)
        # Also set the cell alignment to ensure it's centered
        if self.timer_label.cell():
            self.timer_label.cell().setAlignment_(NSTextAlignmentCenter)
        content_view.addSubview_(self.timer_label)

        # App label (bottom left, small)
        app_rect = NSMakeRect(8, 8, 180, 15)
        self.app_label = NSTextField.alloc().initWithFrame_(app_rect)
        self.app_label.setStringValue_("(starting...)")
        self.app_label.setFont_(NSFont.fontWithName_size_("Menlo", 9))
        self.app_label.setTextColor_(NSColor.whiteColor())
        self.app_label.setBackgroundColor_(NSColor.clearColor())
        self.app_label.setBezeled_(False)
        self.app_label.setDrawsBackground_(False)
        self.app_label.setEditable_(False)
        self.app_label.setSelectable_(False)
        content_view.addSubview_(self.app_label)

        # Status label (bottom right, small)
        status_rect = NSMakeRect(WINDOW_WIDTH - 60, 8, 52, 15)
        self.status_label = NSTextField.alloc().initWithFrame_(status_rect)
        self.status_label.setStringValue_("IDLE")
        self.status_label.setFont_(NSFont.fontWithName_size_("Menlo Bold", 9))
        self.status_label.setTextColor_(NSColor.whiteColor())
        self.status_label.setBackgroundColor_(NSColor.clearColor())
        self.status_label.setBezeled_(False)
        self.status_label.setDrawsBackground_(False)
        self.status_label.setEditable_(False)
        self.status_label.setSelectable_(False)
        self.status_label.setAlignment_(1)  # Right alignment
        content_view.addSubview_(self.status_label)

    def updateTimer_(self, timer):
        """Main update loop - detect active app, idle state, update UI."""
        app_name = get_frontmost_app_name() or "(unknown)"
        idle_seconds = get_idle_seconds()
        allowed = app_name in ALLOWLIST
        is_idle = idle_seconds >= IDLE_THRESHOLD

        # Track recently seen apps (for quick-add in settings)
        if app_name != "(unknown)" and not hasattr(self, '_last_tracked_app'):
            self._last_tracked_app = None

        if app_name != "(unknown)" and app_name != self._last_tracked_app:
            self._last_tracked_app = app_name
            self.track_recent_app(app_name)

        # Working only if app allowed AND user not idle
        self.is_working = allowed and not is_idle

        if self.is_working:
            self.worked_seconds += 1
            self.current_app = app_name

            # Update today's summary
            self.summary[self.today]["total"] += 1
            if app_name not in self.summary[self.today]["by_app"]:
                self.summary[self.today]["by_app"][app_name] = 0
            self.summary[self.today]["by_app"][app_name] += 1

        # Update UI
        status_text = "ACTIVE" if allowed and not is_idle else "IDLE"
        text_color = (
            hex_to_nscolor(GLASS_WORKING_COLOR)
            if self.is_working
            else hex_to_nscolor(GLASS_INACTIVE_COLOR)
        )

        self.timer_label.setStringValue_(format_seconds(self.worked_seconds))
        self.timer_label.setTextColor_(text_color)
        self.app_label.setStringValue_(app_name)
        self.app_label.setTextColor_(text_color)
        self.status_label.setStringValue_(status_text)
        self.status_label.setTextColor_(text_color)


    def quitApp_(self, sender):
        """Handle quit menu action."""
        self.on_close()

    def showSummary_(self, sender):
        """Show work summary window."""
        summary_window = create_summary_window(self.summary, self.today)

        # Keep reference to prevent deallocation and show window
        self.summary_windows.append(summary_window)
        summary_window.makeKeyAndOrderFront_(None)

    def showSettings_(self, sender):
        """Show settings window."""
        try:
            settings_controller = create_settings_controller()

            # Set callback to reload config when settings change
            settings_controller.on_settings_changed = self.reloadConfig

            # Keep reference to prevent deallocation
            self.summary_windows.append(settings_controller)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def resetTimer_(self, sender):
        """Reset the session timer to zero."""
        self.worked_seconds = 0
        self.timer_label.setStringValue_(format_seconds(0))

    def showGuide_(self, sender):
        """Show the user guide window."""
        guide_window = self.create_guide_window()

        # Keep reference to prevent deallocation and show window
        self.summary_windows.append(guide_window)
        guide_window.makeKeyAndOrderFront_(None)

    def create_guide_window(self):
        """Create and return the guide window."""
        # Create guide window with close button
        guide_rect = NSMakeRect(100, 100, 500, 600)
        guide_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            guide_rect,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )

        # Configure window
        guide_window.setTitle_("Sith Guide")
        guide_window.setLevel_(NSFloatingWindowLevel)
        guide_window.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.95))

        # Add glass effect
        from display_utils import add_glass_effect
        add_glass_effect(guide_window)

        # Create scroll view for content
        scroll_rect = guide_window.contentView().bounds()
        scroll_view = NSScrollView.alloc().initWithFrame_(scroll_rect)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setAutoresizingMask_(18)
        scroll_view.setDrawsBackground_(False)

        # Create text view for guide content
        text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 480, 2000))
        text_view.setEditable_(False)
        text_view.setSelectable_(True)
        text_view.setBackgroundColor_(NSColor.clearColor())
        text_view.setTextColor_(NSColor.whiteColor())
        text_view.setFont_(NSFont.fontWithName_size_("Menlo", 12))

        # Load guide content from file
        try:
            from pathlib import Path
            guide_path = Path(__file__).parent / "GUIDE.txt"
            guide_text = guide_path.read_text()
        except Exception:
            guide_text = "Guide file not found. Please check GUIDE.txt in the app directory."

        text_view.setString_(guide_text)

        scroll_view.setDocumentView_(text_view)
        guide_window.contentView().addSubview_(scroll_view)

        # Set window properties
        guide_window.setReleasedWhenClosed_(False)

        return guide_window

    def track_recent_app(self, app_name):
        """Track recently seen app for quick-add suggestions."""
        config_data = load_config()

        # Initialize recent_apps list if not present
        if "recent_apps" not in config_data:
            config_data["recent_apps"] = []

        recent = config_data["recent_apps"]

        # Remove app if already in list (we'll re-add at front)
        if app_name in recent:
            recent.remove(app_name)

        # Add to front of list
        recent.insert(0, app_name)

        # Keep only last 10 apps
        config_data["recent_apps"] = recent[:10]

        # Save to disk
        CONFIG_PATH.write_text(json.dumps(config_data, indent=2))

    def reloadConfig(self):
        """Reload configuration and update display."""
        global config, ALLOWLIST, IDLE_THRESHOLD, GLASS_WORKING_COLOR, GLASS_INACTIVE_COLOR

        # Reload config from file
        config = get_config()
        ALLOWLIST = config.ALLOWLIST
        IDLE_THRESHOLD = config.IDLE_THRESHOLD
        GLASS_WORKING_COLOR = config.GLASS_WORKING_COLOR
        GLASS_INACTIVE_COLOR = config.GLASS_INACTIVE_COLOR

        # Schedule label update on next timer tick instead of blocking here
        # (update_labels will be called in the next timer cycle automatically)

    def add_label(self, window, text, x, y, w, h, bold=False):
        """Helper to add a label to the window."""
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
        label.setStringValue_(text)
        font_name = "Menlo Bold" if bold else "Menlo"
        label.setFont_(NSFont.fontWithName_size_(font_name, 11))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        window.contentView().addSubview_(label)

    def addCurrentApp_(self, sender):
        """Add the current frontmost app to the allowlist."""
        current_app = get_frontmost_app_name()
        if not current_app:
            return

        # Find the settings window
        for window in self.summary_windows:
            if hasattr(window, 'settings_widgets'):
                text_view = window.settings_widgets.get('allowlist_text')
                if text_view:
                    current_text = str(text_view.string())
                    apps = [app.strip() for app in current_text.split('\n') if app.strip()]

                    if current_app not in apps:
                        apps.append(current_app)
                        text_view.setString_('\n'.join(apps))

                break

    def saveSettings_(self, sender):
        """Save settings from the settings window."""
        # Find the settings window
        for window in self.summary_windows:
            if hasattr(window, 'settings_widgets'):
                try:
                    widgets = window.settings_widgets

                    # Get values from UI
                    active_color = widgets['active_color'].color()
                    inactive_color = widgets['inactive_color'].color()
                    idle_timeout = int(widgets['idle_field'].stringValue())

                    # Get allowlist
                    allowlist_text = str(widgets['allowlist_text'].string())
                    allowlist = [app.strip() for app in allowlist_text.split('\n') if app.strip()]

                    # Convert colors to hex
                    active_hex = self.nscolor_to_hex(active_color)
                    inactive_hex = self.nscolor_to_hex(inactive_color)

                    # Load current config and update
                    config = load_config()
                    config["allowlist"] = allowlist
                    config["idle_threshold"] = idle_timeout
                    config["colors"]["glass_working"] = active_hex
                    config["colors"]["glass_inactive"] = inactive_hex

                    # Save to file
                    CONFIG_PATH.write_text(json.dumps(config, indent=2))

                    # Close window
                    window.close()

                    # Show restart message
                    self.show_alert("Settings Saved", "Please restart the app for changes to take effect.")

                except ValueError as e:
                    # Show error
                    self.show_alert("Invalid Input", f"Idle timeout must be a number: {str(e)}")
                except Exception as e:
                    # Show error
                    self.show_alert("Error", f"Could not save: {str(e)}")

                break

    def nscolor_to_hex(self, color):
        """Convert NSColor to hex string."""
        # Convert to RGB color space
        rgb_color = color.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
        if rgb_color:
            r = int(rgb_color.redComponent() * 255)
            g = int(rgb_color.greenComponent() * 255)
            b = int(rgb_color.blueComponent() * 255)
            return f"#{r:02x}{g:02x}{b:02x}"
        return "#ffffff"

    def cancelSettings_(self, sender):
        """Cancel settings editing."""
        # Find and close the settings window
        for window in self.summary_windows:
            if hasattr(window, 'settings_widgets'):
                window.close()
                break

    def show_alert(self, title, message):
        """Show an alert dialog."""
        from Cocoa import NSAlert, NSAlertStyleInformational, NSAlertStyleWarning

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)

        if "Invalid" in title or "Error" in title:
            alert.setAlertStyle_(NSAlertStyleWarning)
        else:
            alert.setAlertStyle_(NSAlertStyleInformational)

        alert.addButtonWithTitle_("OK")
        alert.runModal()

    def windowShouldClose_(self, notification):
        """Handle window close - only for main window."""
        # Only close the app if it's the main window closing
        if notification.object() == self.window:
            self.on_close()
            return True
        # For other windows (like summary), just close them
        return True

    def on_close(self):
        """Save summary and quit."""
        save_summary(self.summary)
        NSApp.terminate_(None)


def main():
    """Main entry point."""
    # Set process name to "Sith" instead of "Python"
    setproctitle.setproctitle("Sith")
    NSProcessInfo.processInfo().setProcessName_("Sith")

    # Create application
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    # Create window controller
    window_controller = SithWindow.alloc().init()

    # Run application
    app.run()


if __name__ == "__main__":
    main()
