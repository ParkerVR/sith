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
)
from Foundation import NSObject, NSMutableArray
import objc

from settings import (
    ALLOWLIST,
    IDLE_THRESHOLD,
    WORKING_COLOR,
    INACTIVE_COLOR,
    TEXT_COLOR,
    GLASS_WORKING_COLOR,
    GLASS_INACTIVE_COLOR,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MARGIN_X,
    WINDOW_MARGIN_Y,
    UPDATE_INTERVAL,
)
from utils import (
    get_frontmost_app_name,
    get_idle_seconds,
    format_seconds,
    load_summary,
    save_summary,
    today_key,
    human_date,
)


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
            self.hex_to_nscolor(GLASS_WORKING_COLOR)
            if self.is_working
            else NSColor.whiteColor()
        )

        self.timer_label.setStringValue_(format_seconds(self.worked_seconds))
        self.timer_label.setTextColor_(text_color)
        self.app_label.setStringValue_(app_name)
        self.app_label.setTextColor_(text_color)
        self.status_label.setStringValue_(status_text)
        self.status_label.setTextColor_(text_color)

    def hex_to_nscolor(self, hex_color):
        """Convert hex color string to NSColor."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0)

    def quitApp_(self, sender):
        """Handle quit menu action."""
        self.on_close()

    def showSummary_(self, sender):
        """Show work summary window."""
        # Create summary window with close button
        summary_rect = NSMakeRect(100, 100, 380, 440)
        summary_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            summary_rect,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )

        # Configure window
        summary_window.setTitle_("Work Summary")
        summary_window.setLevel_(NSFloatingWindowLevel)
        summary_window.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.95))

        # Add glass effect
        effect_view = NSVisualEffectView.alloc().initWithFrame_(
            summary_window.contentView().bounds()
        )
        effect_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
        effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        effect_view.setState_(1)
        effect_view.setAutoresizingMask_(18)
        summary_window.contentView().addSubview_(effect_view)

        # Start from top of content area
        y_position = 380

        # Sort entries by date (most recent first)
        for day in sorted(self.summary.keys(), reverse=True):
            day_data = self.summary[day]
            total_s = day_data["total"]
            by_app = day_data.get("by_app", {})

            # Date header with total
            date_text = f"{human_date(day):14s} {format_seconds(total_s):>8s}"
            is_today = day == self.today

            date_rect = NSMakeRect(20, y_position, 340, 18)
            date_label = NSTextField.alloc().initWithFrame_(date_rect)
            date_label.setStringValue_(date_text)
            date_label.setFont_(
                NSFont.fontWithName_size_(
                    "Menlo Bold" if is_today else "Menlo", 10
                )
            )
            date_label.setTextColor_(NSColor.whiteColor())
            date_label.setBackgroundColor_(NSColor.clearColor())
            date_label.setBezeled_(False)
            date_label.setDrawsBackground_(False)
            date_label.setEditable_(False)
            date_label.setSelectable_(False)
            summary_window.contentView().addSubview_(date_label)
            y_position -= 20

            # Per-app breakdown
            if by_app:
                for app_name in sorted(by_app.keys()):
                    app_seconds = by_app[app_name]
                    app_text = f"  {app_name:20s} {format_seconds(app_seconds):>8s}"

                    app_rect = NSMakeRect(20, y_position, 340, 15)
                    app_label = NSTextField.alloc().initWithFrame_(app_rect)
                    app_label.setStringValue_(app_text)
                    app_label.setFont_(NSFont.fontWithName_size_("Menlo", 9))
                    app_label.setTextColor_(
                        NSColor.colorWithCalibratedWhite_alpha_(0.9, 1.0)
                    )
                    app_label.setBackgroundColor_(NSColor.clearColor())
                    app_label.setBezeled_(False)
                    app_label.setDrawsBackground_(False)
                    app_label.setEditable_(False)
                    app_label.setSelectable_(False)
                    summary_window.contentView().addSubview_(app_label)
                    y_position -= 16

            y_position -= 8  # Extra space between days

        # Make sure summary window doesn't use our delegate
        summary_window.setDelegate_(None)

        # Set releasedWhenClosed to False to prevent crashes
        summary_window.setReleasedWhenClosed_(False)

        # Keep reference to prevent deallocation and show window
        self.summary_windows.append(summary_window)
        summary_window.makeKeyAndOrderFront_(None)

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
    # Create application
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    # Create window controller
    window_controller = WorkClockWindow.alloc().init()

    # Run application
    app.run()


if __name__ == "__main__":
    main()
