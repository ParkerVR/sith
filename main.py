"""
Work Clock - Main application window and entry point.
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
from settings_window import create_settings_window

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


class WorkClockWindow(NSObject):
    """Main work clock window using native Cocoa."""

    def init(self):
        self = objc.super(WorkClockWindow, self).init()
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

        # Settings 2 menu item (test)
        settings2_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings Test", "showSettings2:", ""
        )
        settings2_item.setTarget_(self)
        self.menu.addItem_(settings2_item)

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
            else NSColor.whiteColor()
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

    def showSettings2_(self, sender):
        """Show settings window."""
        print("showSettings2_ called")
        try:
            settings_window, widgets = create_settings_window()
            print(f"Settings window created: {settings_window}")

            # Keep reference to prevent deallocation and show window
            self.summary_windows.append(settings_window)
            print("About to show window")
            settings_window.makeKeyAndOrderFront_(None)
            print("Window shown")
        except Exception as e:
            print(f"Error creating settings window: {e}")
            import traceback
            traceback.print_exc()

    def showSettings_(self, sender):
        """Show settings window with native UI controls."""
        # Create settings window - exactly like summary window
        settings_rect = NSMakeRect(100, 100, 520, 480)
        settings_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            settings_rect,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )

        # Configure window
        settings_window.setTitle_("Settings")
        settings_window.setLevel_(NSFloatingWindowLevel)
        settings_window.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.95))

        # Add glass effect
        effect_view = NSVisualEffectView.alloc().initWithFrame_(
            settings_window.contentView().bounds()
        )
        effect_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
        effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        effect_view.setState_(1)
        effect_view.setAutoresizingMask_(18)
        settings_window.contentView().addSubview_(effect_view)

        # Load current config
        current_config = load_config()

        # Store UI elements as window attributes for later access
        settings_window.settings_widgets = {}

        y_pos = 420

        # === Colors Section ===
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 480, 20))
        label.setStringValue_("Colors")
        label.setFont_(NSFont.fontWithName_size_("Menlo Bold", 11))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        settings_window.contentView().addSubview_(label)
        y_pos -= 30

        # Active color
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 150, 20))
        label.setStringValue_("Active Text Color:")
        label.setFont_(NSFont.fontWithName_size_("Menlo", 11))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        settings_window.contentView().addSubview_(label)

        active_color_well = NSColorWell.alloc().initWithFrame_(NSMakeRect(180, y_pos, 60, 25))
        active_color = self.hex_to_nscolor(current_config.get("colors", {}).get("glass_working", "#00d4ff"))
        active_color_well.setColor_(active_color)
        settings_window.contentView().addSubview_(active_color_well)
        settings_window.settings_widgets['active_color'] = active_color_well
        y_pos -= 35

        # Inactive color
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 150, 20))
        label.setStringValue_("Inactive Text Color:")
        label.setFont_(NSFont.fontWithName_size_("Menlo", 11))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        settings_window.contentView().addSubview_(label)

        inactive_color_well = NSColorWell.alloc().initWithFrame_(NSMakeRect(180, y_pos, 60, 25))
        inactive_color = self.hex_to_nscolor(current_config.get("colors", {}).get("glass_inactive", "#ffffff"))
        inactive_color_well.setColor_(inactive_color)
        settings_window.contentView().addSubview_(inactive_color_well)
        settings_window.settings_widgets['inactive_color'] = inactive_color_well
        y_pos -= 45

        # === Idle Timeout Section ===
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 480, 20))
        label.setStringValue_("Idle Timeout")
        label.setFont_(NSFont.fontWithName_size_("Menlo Bold", 11))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        settings_window.contentView().addSubview_(label)
        y_pos -= 30

        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 150, 20))
        label.setStringValue_("Idle after (seconds):")
        label.setFont_(NSFont.fontWithName_size_("Menlo", 11))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        settings_window.contentView().addSubview_(label)

        idle_field = NSTextField.alloc().initWithFrame_(NSMakeRect(180, y_pos, 60, 22))
        idle_field.setStringValue_(str(current_config.get("idle_threshold", 2)))
        idle_field.setFont_(NSFont.fontWithName_size_("Menlo", 12))
        idle_field.setTextColor_(NSColor.blackColor())
        settings_window.contentView().addSubview_(idle_field)
        settings_window.settings_widgets['idle_field'] = idle_field
        y_pos -= 45

        # === App Allowlist Section ===
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 480, 20))
        label.setStringValue_("Tracked Applications")
        label.setFont_(NSFont.fontWithName_size_("Menlo Bold", 11))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        settings_window.contentView().addSubview_(label)
        y_pos -= 25

        # Get current allowlist
        allowlist = current_config.get("allowlist", [])

        # Create text view for allowlist
        allowlist_rect = NSMakeRect(20, y_pos - 120, 320, 140)
        allowlist_scroll = NSScrollView.alloc().initWithFrame_(allowlist_rect)
        allowlist_scroll.setHasVerticalScroller_(True)
        allowlist_scroll.setBorderType_(NSBezelBorder)

        allowlist_text = NSTextView.alloc().initWithFrame_(allowlist_scroll.contentView().bounds())
        allowlist_text.setString_("\n".join(allowlist))
        allowlist_text.setFont_(NSFont.fontWithName_size_("Menlo", 11))
        allowlist_text.setTextColor_(NSColor.whiteColor())
        allowlist_text.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.1, 0.9))
        allowlist_text.setEditable_(True)

        allowlist_scroll.setDocumentView_(allowlist_text)
        settings_window.contentView().addSubview_(allowlist_scroll)
        settings_window.settings_widgets['allowlist_text'] = allowlist_text

        # Add button to add current app
        add_current_btn = NSButton.alloc().initWithFrame_(NSMakeRect(350, y_pos - 30, 150, 28))
        add_current_btn.setTitle_("Add Current App")
        add_current_btn.setBezelStyle_(NSBezelStyleRounded)
        add_current_btn.setTarget_(self)
        add_current_btn.setAction_("addCurrentApp:")
        settings_window.contentView().addSubview_(add_current_btn)

        # Help text
        help_text = NSTextField.alloc().initWithFrame_(NSMakeRect(350, y_pos - 90, 150, 50))
        help_text.setStringValue_("Add apps by name,\none per line.\n\nCurrent app shown\nin main HUD.")
        help_text.setFont_(NSFont.fontWithName_size_("Menlo", 9))
        help_text.setTextColor_(NSColor.colorWithCalibratedWhite_alpha_(0.6, 1.0))
        help_text.setBackgroundColor_(NSColor.clearColor())
        help_text.setBezeled_(False)
        help_text.setDrawsBackground_(False)
        help_text.setEditable_(False)
        help_text.setSelectable_(False)
        settings_window.contentView().addSubview_(help_text)

        # === Buttons ===
        # Save button
        save_button = NSButton.alloc().initWithFrame_(NSMakeRect(380, 15, 120, 32))
        save_button.setTitle_("Save & Restart")
        save_button.setBezelStyle_(NSBezelStyleRounded)
        save_button.setTarget_(self)
        save_button.setAction_("saveSettings:")
        settings_window.contentView().addSubview_(save_button)

        # Cancel button
        cancel_button = NSButton.alloc().initWithFrame_(NSMakeRect(250, 15, 120, 32))
        cancel_button.setTitle_("Cancel")
        cancel_button.setBezelStyle_(NSBezelStyleRounded)
        cancel_button.setTarget_(self)
        cancel_button.setAction_("cancelSettings:")
        settings_window.contentView().addSubview_(cancel_button)

        # Make sure settings window doesn't use our delegate
        settings_window.setDelegate_(None)

        # Set releasedWhenClosed to False to prevent crashes
        settings_window.setReleasedWhenClosed_(False)

        # Keep reference to prevent deallocation and show window
        self.summary_windows.append(settings_window)
        settings_window.makeKeyAndOrderFront_(None)

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
    # Set process name to "Work Clock" instead of "Python"
    setproctitle.setproctitle("Work Clock")
    NSProcessInfo.processInfo().setProcessName_("Work Clock")

    # Create application
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    # Create window controller
    window_controller = WorkClockWindow.alloc().init()

    # Run application
    app.run()


if __name__ == "__main__":
    main()
