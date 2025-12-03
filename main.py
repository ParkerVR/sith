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
    NSNormalWindowLevel,
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
    NSAnimationContext,
    NSRightMouseDown,
    NSLeftMouseDown,
    NSLeftMouseDragged,
    NSApp,
    NSApplicationActivationPolicyAccessory,
    NSScreen,
    NSButton,
    NSBezelStyleRounded,
    NSTextAlignmentCenter,
    NSTextAlignmentRight,
    NSTextView,
    NSCalibratedRGBColorSpace,
    NSScrollView,
    NSMakeSize,
    NSColorWell,
    NSSlider,
    NSTableView,
    NSTableColumn,
    NSBezelBorder,
    NSPopUpButton,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSImage,
    NSOnState,
    NSOffState,
    NSAlert,
    NSWorkspace,
    NSURL,
    NSAttributedString,
)
from Foundation import NSObject, NSMutableArray, NSProcessInfo, NSDate, NSData
import objc
import setproctitle
import json
import markdown
from pathlib import Path

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
    check_accessibility_permission,
    request_accessibility_permission,
)
from display_utils import hex_to_nscolor, nscolor_to_hex, get_font
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

# UI layout constants
LABEL_MARGIN_X = 8  # Horizontal margin from edges for bottom labels
LABEL_MARGIN_Y = 8  # Vertical margin from bottom for bottom labels
STATUS_LABEL_WIDTH = 52  # Width of status label

TIMER_FONT_SIZE = 30


class WindowDelegate(NSObject):
    """Delegate to handle window close events."""

    def initWithCallback_(self, callback):
        self = objc.super(WindowDelegate, self).init()
        if self is None:
            return None
        self.callback = callback
        return self

    def windowWillClose_(self, notification):
        """Called when window is about to close."""
        if self.callback:
            self.callback()


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

        # Color animation state
        self.previous_text_color = None
        self.color_anim_timer = None
        self.color_anim_start_time = 0.0
        self.color_anim_duration = 0.3  # seconds (quicker animation)
        self.color_anim_from = None
        self.color_anim_to = None

        # Load settings from config
        config_data = load_config()
        self.color_animation_enabled = config_data.get("enable_color_animation", True)
        self.show_status_bar = config_data.get("show_status_bar", True)
        self.time_display_style = config_data.get("time_display_style", "HH:MM:SS")
        self.timer_font_family = config_data.get("timer_font_family", "Menlo")

        # Drag state
        self.drag_offset = None

        # Track individual windows to prevent duplicates
        self.settings_window = None
        self.guide_window = None
        self.summary_window = None

        # Store menu items for dynamic updates
        self.summary_menu_item = None
        self.settings_menu_item = None
        self.guide_menu_item = None

        # Status bar item (initially not created)
        self.status_item = None
        self.window_visible = True

        # Permission dialog state - only show once per session
        self.permission_dialog_shown = False

        # Initialize today's entry if needed
        if self.today not in self.summary:
            self.summary[self.today] = {"total": 0, "by_app": {}}

        # Create window
        self.create_window()

        # Check and request accessibility permission if needed
        self.check_permissions()

        # Start update timer with tolerance for energy efficiency
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            UPDATE_INTERVAL / 1000.0,  # Convert ms to seconds
            self,
            "updateTimer:",
            None,
            True,
        )
        # Set tolerance to ~10% for better timer coalescing (Apple recommendation)
        self.timer.setTolerance_(UPDATE_INTERVAL / 1000.0 * 0.1)

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
        # Timer window floats above other windows - this is a utility HUD that should always be visible
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setMovableByWindowBackground_(True)

        # Accessibility
        self.window.setAccessibilityTitle_("Sith Timer")
        self.window.setAccessibilityHelp_("Floating timer window showing work time tracking")

        # Add rounded corners (Apple standard)
        self.window.contentView().setWantsLayer_(True)
        self.window.contentView().layer().setCornerRadius_(10.0)
        self.window.contentView().layer().setMasksToBounds_(True)

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

        # Set delegate to update menu items before showing
        self.menu.setDelegate_(self)

        # Work Summary menu item (uses checkmark to show state)
        self.summary_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Work Summary", "toggleSummary:", ""
        )
        self.summary_menu_item.setTarget_(self)
        self.summary_menu_item.setAccessibilityHelp_("Open window showing work time breakdown by day and app")
        self.menu.addItem_(self.summary_menu_item)

        # Settings menu item (uses checkmark to show state)
        self.settings_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings", "toggleSettings:", ""
        )
        self.settings_menu_item.setTarget_(self)
        self.settings_menu_item.setAccessibilityHelp_("Configure app allowlist, colors, and behavior")
        self.menu.addItem_(self.settings_menu_item)

        # Guide menu item (uses checkmark to show state)
        self.guide_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Guide", "toggleGuide:", ""
        )
        self.guide_menu_item.setTarget_(self)
        self.guide_menu_item.setAccessibilityHelp_("View user guide and documentation")
        self.menu.addItem_(self.guide_menu_item)

        # Reset Timer menu item
        reset_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Reset Timer", "resetTimer:", ""
        )
        reset_item.setTarget_(self)
        reset_item.setAccessibilityHelp_("Reset work time counter to zero for current session")
        self.menu.addItem_(reset_item)

        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())

        # Minimize to Status Bar menu item
        minimize_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Minimize to Status Bar", "minimizeToStatusBar:", ""
        )
        minimize_item.setTarget_(self)
        minimize_item.setAccessibilityHelp_("Hide window and show status bar icon only")
        self.menu.addItem_(minimize_item)

        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())

        # Quit menu item
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", "q"
        )
        quit_item.setTarget_(self)
        quit_item.setAccessibilityHelp_("Quit Sith")
        self.menu.addItem_(quit_item)

        # Enable right-click on content view
        self.window.contentView().setMenu_(self.menu)

    def menuNeedsUpdate_(self, menu):
        """Called automatically before menu is displayed - updates menu items."""
        self.update_menu_items()

    def update_menu_items(self):
        """Update menu item states with checkmarks based on window visibility."""
        # Summary menu - show checkmark when window is visible
        if self.summary_window and self.summary_window.isVisible():
            self.summary_menu_item.setState_(NSOnState)
        else:
            self.summary_menu_item.setState_(NSOffState)

        # Settings menu - show checkmark when window is visible
        if self.settings_window and self.settings_window.window and self.settings_window.window.isVisible():
            self.settings_menu_item.setState_(NSOnState)
        else:
            self.settings_menu_item.setState_(NSOffState)

        # Guide menu - show checkmark when window is visible
        if self.guide_window and self.guide_window.isVisible():
            self.guide_menu_item.setState_(NSOnState)
        else:
            self.guide_menu_item.setState_(NSOffState)

    def check_permissions(self):
        """Check for required permissions and request if needed."""
        # Only show dialog once per session
        if not self.permission_dialog_shown and not check_accessibility_permission():
            self.permission_dialog_shown = True
            self.show_permission_dialog()

    def show_permission_dialog(self):
        """Show a dialog explaining permission requirements."""
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Accessibility Permission Required")
        alert.setInformativeText_(
            "Sith needs Accessibility permission to detect which app you're currently using.\n\n"
            "Without this permission, the timer won't be able to track your work time.\n\n"
            "Click 'Open System Settings' to grant permission, then restart Sith."
        )
        alert.addButtonWithTitle_("Open System Settings")
        alert.addButtonWithTitle_("Later")
        alert.setAlertStyle_(1)  # Informational style

        response = alert.runModal()

        if response == 1000:  # First button (Open System Settings)
            # Open System Settings to Privacy & Security > Accessibility
            from Cocoa import NSURL
            workspace = NSWorkspace.sharedWorkspace()
            # Open the Accessibility pane in System Settings
            url = NSURL.URLWithString_("x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")
            workspace.openURL_(url)
        # If "Later" is clicked, just close the dialog

    def create_labels(self):
        """Create text labels for timer, app name, and status."""
        content_view = self.window.contentView()


        # Timer label (large, centered)
        # NOTE: Timer uses custom colors (not semantic) as a core feature -
        # colors are user-configurable and change based on work state
        # Timer font is configurable in settings
        # Keep timer at same vertical position regardless of status bar visibility
        timer_y = 20
        timer_rect = NSMakeRect(0, timer_y, WINDOW_WIDTH, 35)
        self.timer_label = NSTextField.alloc().initWithFrame_(timer_rect)
        self.timer_label.setStringValue_("00:00:00")
        self.timer_label.setFont_(get_font(self.timer_font_family, TIMER_FONT_SIZE, bold=True))
        # Initial color - will be updated by updateTimer_ based on work state
        self.timer_label.setTextColor_(NSColor.whiteColor())
        self.timer_label.setBackgroundColor_(NSColor.clearColor())
        self.timer_label.setBezeled_(False)
        self.timer_label.setDrawsBackground_(False)
        self.timer_label.setEditable_(False)
        self.timer_label.setSelectable_(False)
        self.timer_label.setAlignment_(NSTextAlignmentCenter)
        self.timer_label.setWantsLayer_(True)  # Enable layer for smooth animations
        # Also set the cell alignment to ensure it's centered
        if self.timer_label.cell():
            self.timer_label.cell().setAlignment_(NSTextAlignmentCenter)
        # Accessibility
        self.timer_label.setAccessibilityLabel_("Work time")
        self.timer_label.setAccessibilityHelp_("Total time worked in current session")
        content_view.addSubview_(self.timer_label)

        # App label (bottom left, small)
        # NOTE: Uses same custom color system as timer for visual consistency
        # Always uses SF Pro for UI consistency
        app_rect = NSMakeRect(LABEL_MARGIN_X, LABEL_MARGIN_Y, 180, 15)
        self.app_label = NSTextField.alloc().initWithFrame_(app_rect)
        self.app_label.setStringValue_("(starting...)")
        self.app_label.setFont_(get_font("SF Pro", 9, bold=False))
        self.app_label.setTextColor_(NSColor.whiteColor())
        self.app_label.setBackgroundColor_(NSColor.clearColor())
        self.app_label.setBezeled_(False)
        self.app_label.setDrawsBackground_(False)
        self.app_label.setEditable_(False)
        self.app_label.setSelectable_(False)
        self.app_label.setWantsLayer_(True)  # Enable layer for smooth animations
        # Accessibility
        self.app_label.setAccessibilityLabel_("Current application")
        self.app_label.setAccessibilityHelp_("Name of the currently active application")
        content_view.addSubview_(self.app_label)

        # Status label (bottom right, small)
        # NOTE: Uses same custom color system as timer for visual consistency
        # Always uses SF Pro for UI consistency
        status_rect = NSMakeRect(WINDOW_WIDTH - STATUS_LABEL_WIDTH - LABEL_MARGIN_X, LABEL_MARGIN_Y, STATUS_LABEL_WIDTH, 15)
        self.status_label = NSTextField.alloc().initWithFrame_(status_rect)
        self.status_label.setStringValue_("IDLE")
        self.status_label.setFont_(get_font("SF Pro", 9, bold=True))
        self.status_label.setTextColor_(NSColor.whiteColor())
        self.status_label.setBackgroundColor_(NSColor.clearColor())
        self.status_label.setBezeled_(False)
        self.status_label.setDrawsBackground_(False)
        self.status_label.setEditable_(False)
        self.status_label.setSelectable_(False)
        self.status_label.setAlignment_(NSTextAlignmentRight)
        self.status_label.setWantsLayer_(True)  # Enable layer for smooth animations
        # Accessibility
        self.status_label.setAccessibilityLabel_("Work status")
        self.status_label.setAccessibilityHelp_("Indicates whether actively tracking work time or idle")
        content_view.addSubview_(self.status_label)

        # Set initial visibility based on show_status_bar setting
        self.app_label.setHidden_(not self.show_status_bar)
        self.status_label.setHidden_(not self.show_status_bar)

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
            # Increment by actual elapsed time (in seconds)
            elapsed = UPDATE_INTERVAL / 1000.0
            self.worked_seconds += elapsed
            self.current_app = app_name

            # Update today's summary
            self.summary[self.today]["total"] += elapsed
            if app_name not in self.summary[self.today]["by_app"]:
                self.summary[self.today]["by_app"][app_name] = 0
            self.summary[self.today]["by_app"][app_name] += elapsed

        # Update UI
        status_text = "ACTIVE" if allowed and not is_idle else "IDLE"
        text_color = (
            hex_to_nscolor(GLASS_WORKING_COLOR)
            if self.is_working
            else hex_to_nscolor(GLASS_INACTIVE_COLOR)
        )

        # Display timer (convert float to int for clean display)
        self.timer_label.setStringValue_(format_seconds(int(self.worked_seconds), self.time_display_style))
        self.app_label.setStringValue_(app_name)
        self.status_label.setStringValue_(status_text)

        # Only animate color transitions when color actually changes
        color_changed = (self.previous_text_color is None or
                        text_color != self.previous_text_color)

        if color_changed:
            # Check if color animation is enabled
            if self.color_animation_enabled:
                # Animate color transitions with manual RGB interpolation
                self._start_text_color_animation(text_color)
            else:
                # No animation, instant color change
                self.timer_label.setTextColor_(text_color)
                self.app_label.setTextColor_(text_color)
                self.status_label.setTextColor_(text_color)
                self.previous_text_color = text_color
        else:
            # No color change needed
            self.timer_label.setTextColor_(text_color)
            self.app_label.setTextColor_(text_color)
            self.status_label.setTextColor_(text_color)

    def _color_to_rgba(self, color):
        """Convert NSColor to an (r, g, b, a) tuple in calibrated RGB space."""
        if color is None:
            return (1.0, 1.0, 1.0, 1.0)  # default white

        c = color.colorUsingColorSpaceName_(NSCalibratedRGBColorSpace)
        if c is None:
            return (1.0, 1.0, 1.0, 1.0)

        return (
            c.redComponent(),
            c.greenComponent(),
            c.blueComponent(),
            c.alphaComponent(),
        )

    def _rgba_lerp(self, rgba_from, rgba_to, t):
        """Linear interpolation between two RGBA tuples."""
        return tuple(
            f + (t * (tgt - f)) for f, tgt in zip(rgba_from, rgba_to)
        )

    def _start_text_color_animation(self, new_color):
        """Start a smooth color animation to new_color."""
        # Cancel any previous animation
        if self.color_anim_timer is not None:
            self.color_anim_timer.invalidate()
            self.color_anim_timer = None

        # Determine starting color: previous, or current label color
        if self.previous_text_color is not None:
            from_color = self.previous_text_color
        else:
            from_color = self.timer_label.textColor()  # current actual color

        self.color_anim_from = self._color_to_rgba(from_color)
        self.color_anim_to = self._color_to_rgba(new_color)
        self.color_anim_start_time = NSDate.timeIntervalSinceReferenceDate()

        # Set previous_text_color immediately to the final target
        self.previous_text_color = new_color

        # 30 FPS animation
        self.color_anim_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / 30.0,
            self,
            "stepColorAnimation:",
            None,
            True,
        )

    def stepColorAnimation_(self, timer):
        """Step function for color animation - interpolates RGB values."""
        now = NSDate.timeIntervalSinceReferenceDate()
        elapsed = now - self.color_anim_start_time
        t = elapsed / self.color_anim_duration

        if t >= 1.0:
            t = 1.0

        rgba = self._rgba_lerp(self.color_anim_from, self.color_anim_to, t)
        r, g, b, a = rgba

        blended = NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

        self.timer_label.setTextColor_(blended)
        self.app_label.setTextColor_(blended)
        self.status_label.setTextColor_(blended)

        if t >= 1.0:
            # Done, snap to final and clean up
            self.color_anim_timer.invalidate()
            self.color_anim_timer = None
            # Ensure exact final color
            self.timer_label.setTextColor_(self.previous_text_color)
            self.app_label.setTextColor_(self.previous_text_color)
            self.status_label.setTextColor_(self.previous_text_color)


    def quitApp_(self, sender):
        """Handle quit menu action."""
        self.on_close()

    def minimizeToStatusBar_(self, sender):
        """Hide window and show status bar icon."""
        if not self.status_item:
            self.create_status_bar_item()
        self.window.orderOut_(None)
        self.window_visible = False

    def create_status_bar_item(self):
        """Create status bar item with icon and menu."""
        status_bar = NSStatusBar.systemStatusBar()
        self.status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)

        # Try to load custom status bar icon, fallback to SF Symbol
        icon = None
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "statusbar_icon.png")
            if os.path.exists(icon_path):
                icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
        except Exception as e:
            print(f"Could not load custom icon: {e}")

        # Fallback to SF Symbol if custom icon not found
        if not icon:
            icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                "clock.fill", "Sith Timer"
            )

        if icon and self.status_item.button():
            # Make it a template image so it adapts to light/dark mode
            icon.setTemplate_(True)
            self.status_item.button().setImage_(icon)

        # Accessibility
        if self.status_item.button():
            self.status_item.button().setAccessibilityLabel_("Sith")
            self.status_item.button().setAccessibilityHelp_("Sith work time tracking app. Click to show menu.")

        # Create menu for status bar item
        status_menu = NSMenu.alloc().init()

        # Show Window item
        show_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show Window", "toggleWindowVisibility:", ""
        )
        show_item.setTarget_(self)
        show_item.setAccessibilityHelp_("Show the main timer window")
        status_menu.addItem_(show_item)

        # Separator
        status_menu.addItem_(NSMenuItem.separatorItem())

        # Quit item
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", "q"
        )
        quit_item.setTarget_(self)
        quit_item.setAccessibilityHelp_("Quit Sith")
        status_menu.addItem_(quit_item)

        self.status_item.setMenu_(status_menu)

    def toggleWindowVisibility_(self, sender):
        """Toggle window visibility from status bar."""
        if self.window_visible:
            self.window.orderOut_(None)
            self.window_visible = False
        else:
            self.window.makeKeyAndOrderFront_(None)
            self.window_visible = True
            # Remove status bar item when showing window
            if self.status_item:
                NSStatusBar.systemStatusBar().removeStatusItem_(self.status_item)
                self.status_item = None

    def toggleSummary_(self, sender):
        """Toggle work summary window (only one allowed)."""
        # If summary window exists and is visible, close it
        if self.summary_window and self.summary_window.isVisible():
            self.summary_window.close()
            return

        # Otherwise, create new summary window
        summary_window = create_summary_window(self.summary, self.today)

        # Set up delegate to track window closing
        delegate = WindowDelegate.alloc().initWithCallback_(self.on_summary_closed)
        summary_window.setDelegate_(delegate)

        # Store reference and show window
        self.summary_window = summary_window
        summary_window.makeKeyAndOrderFront_(None)
        self.update_menu_items()

    def on_summary_closed(self):
        """Called when summary window closes."""
        self.summary_window = None
        self.update_menu_items()

    def toggleSettings_(self, sender):
        """Toggle settings window (only one allowed)."""
        # If settings window exists and is visible, close it
        if self.settings_window and self.settings_window.window and self.settings_window.window.isVisible():
            self.settings_window.window.close()
            return

        # Otherwise, create new settings window
        try:
            settings_controller = create_settings_controller()

            # Set callback to reload config when settings change
            settings_controller.on_settings_changed = self.reloadConfig

            # Set up delegate to track window closing
            delegate = WindowDelegate.alloc().initWithCallback_(self.on_settings_closed)
            settings_controller.window.setDelegate_(delegate)

            # Store reference and update menu
            self.settings_window = settings_controller
            self.update_menu_items()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def on_settings_closed(self):
        """Called when settings window closes."""
        self.settings_window = None
        self.update_menu_items()

    def resetTimer_(self, sender):
        """Reset the session timer to zero."""
        self.worked_seconds = 0
        self.timer_label.setStringValue_(format_seconds(0, self.time_display_style))

    def toggleGuide_(self, sender):
        """Toggle guide window (only one allowed)."""
        # If guide window exists and is visible, close it
        if self.guide_window and self.guide_window.isVisible():
            self.guide_window.close()
            return

        # Otherwise, create new guide window
        guide_window = self.create_guide_window()

        # Set up delegate to track window closing
        delegate = WindowDelegate.alloc().initWithCallback_(self.on_guide_closed)
        guide_window.setDelegate_(delegate)

        # Store reference and show window
        self.guide_window = guide_window
        guide_window.makeKeyAndOrderFront_(None)
        self.update_menu_items()

    def on_guide_closed(self):
        """Called when guide window closes."""
        self.guide_window = None
        self.update_menu_items()

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
        # Use normal window level - guide window doesn't need to float above everything
        guide_window.setLevel_(NSNormalWindowLevel)
        # Use system background color with transparency for proper appearance adaptation
        guide_window.setBackgroundColor_(NSColor.windowBackgroundColor().colorWithAlphaComponent_(0.95))

        # Accessibility
        guide_window.setAccessibilityHelp_("User guide and instructions for using Sith")

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

        # Load guide content from file and parse as markdown
        guide_path = Path(__file__).parent / "GUIDE.md"
        guide_markdown = guide_path.read_text()

        # Convert markdown to HTML
        html_content = markdown.markdown(guide_markdown)

        # Wrap in basic HTML structure with styling
        html_full = f"""
        <html>
        <head>
            <meta name="color-scheme" content="light dark">
            <style>
                body {{
                    font-family: -apple-system;
                    font-size: 13px;
                    line-height: 1.5;
                    padding: 10px;
                    color-scheme: light dark;
                }}
                h1 {{ font-size: 24px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; }}
                h2 {{ font-size: 18px; font-weight: bold; margin-top: 16px; margin-bottom: 8px; }}
                h3 {{ font-size: 15px; font-weight: bold; margin-top: 12px; margin-bottom: 6px; }}
                p {{ margin: 8px 0; }}
                ul, ol {{ margin: 8px 0; padding-left: 20px; }}
                li {{ margin: 4px 0; }}
                code {{ font-family: 'SF Mono', Menlo, monospace; background-color: rgba(128,128,128,0.15); padding: 2px 4px; border-radius: 3px; }}
                pre {{ font-family: 'SF Mono', Menlo, monospace; background-color: rgba(128,128,128,0.15); padding: 10px; border-radius: 5px; overflow-x: auto; }}
                hr {{ border: none; border-top: 1px solid rgba(128,128,128,0.3); margin: 16px 0; }}
            </style>
        </head>
        <body>{html_content}</body>
        </html>
        """

        # Convert HTML to NSAttributedString
        html_data = html_full.encode('utf-8')
        ns_data = NSData.alloc().initWithBytes_length_(html_data, len(html_data))
        attributed_string = NSAttributedString.alloc().initWithHTML_documentAttributes_(ns_data, None)[0]

        # Apply the attributed string
        text_view.textStorage().setAttributedString_(attributed_string)

        # Post-process to apply semantic text color throughout
        text_storage = text_view.textStorage()
        full_range = (0, text_storage.length())
        semantic_color = NSColor.labelColor()
        text_storage.addAttribute_value_range_("NSColor", semantic_color, full_range)

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
        config_data = load_config()
        ALLOWLIST = config.ALLOWLIST
        IDLE_THRESHOLD = config.IDLE_THRESHOLD
        GLASS_WORKING_COLOR = config.GLASS_WORKING_COLOR
        GLASS_INACTIVE_COLOR = config.GLASS_INACTIVE_COLOR

        # Reload settings
        self.color_animation_enabled = config_data.get("enable_color_animation", True)
        self.show_status_bar = config_data.get("show_status_bar", True)
        self.time_display_style = config_data.get("time_display_style", "HH:MM:SS")
        self.timer_font_family = config_data.get("timer_font_family", "Menlo")

        # Update fonts immediately
        # Timer uses configurable font, UI elements always use SF Pro
        self.timer_label.setFont_(get_font(self.timer_font_family, TIMER_FONT_SIZE, bold=True))
        self.app_label.setFont_(get_font("SF Pro", 9, bold=False))
        self.status_label.setFont_(get_font("SF Pro", 9, bold=True))

        # Update status bar visibility and timer position
        self.app_label.setHidden_(not self.show_status_bar)
        self.status_label.setHidden_(not self.show_status_bar)

        # Keep timer at same vertical position regardless of status bar visibility
        timer_y = 20
        self.timer_label.setFrame_(NSMakeRect(0, timer_y, WINDOW_WIDTH, 35))

        # Schedule label update on next timer tick instead of blocking here
        # (update_labels will be called in the next timer cycle automatically)

    def add_label(self, window, text, x, y, w, h, bold=False):
        """Helper to add a label to the window."""
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
        label.setStringValue_(text)
        label.setFont_(get_font("SF Pro", 11, bold=bold))
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

        # Update settings window if it's open
        if self.settings_window and hasattr(self.settings_window, 'settings_widgets'):
            text_view = self.settings_window.settings_widgets.get('allowlist_text')
            if text_view:
                current_text = str(text_view.string())
                apps = [app.strip() for app in current_text.split('\n') if app.strip()]

                if current_app not in apps:
                    apps.append(current_app)
                    text_view.setString_('\n'.join(apps))

    def saveSettings_(self, sender):
        """Save settings from the settings window."""
        # Use tracked settings window
        if self.settings_window and hasattr(self.settings_window, 'settings_widgets'):
            try:
                widgets = self.settings_window.settings_widgets

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
                self.settings_window.close()

                # Show restart message
                self.show_alert("Settings Saved", "Please restart the app for changes to take effect.")

            except ValueError as e:
                # Show error
                self.show_alert("Invalid Input", f"Idle timeout must be a number: {str(e)}")
            except Exception as e:
                # Show error
                self.show_alert("Error", f"Could not save: {str(e)}")

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
        # Close settings window if open
        if self.settings_window:
            self.settings_window.close()

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
