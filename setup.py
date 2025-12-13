"""
Setup script for creating a standalone macOS .app bundle.
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('assets', ['assets/generated/statusbar_icon.png', 'assets/generated/statusbar_icon@2x.png']),
    ('', ['GUIDE.md'])  # Include guide in Resources root
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/generated/AppIcon.icns',
    'plist': {
        'CFBundleName': 'Sith',
        'CFBundleDisplayName': 'Sith',
        'CFBundleIdentifier': 'com.parkervanroy.sith',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Makes it a menubar/background app (no dock icon)
        'NSHighResolutionCapable': True,
        # Privacy strings required for App Store
        'NSAppleEventsUsageDescription': 'Sith needs to know which app you\'re using to track your work time accurately.',
        # App Store metadata
        'LSMinimumSystemVersion': '10.15.0',
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSHumanReadableCopyright': 'Copyright © 2025 Parker Van Roy. All rights reserved.',
    },
    'packages': ['objc', 'Cocoa', 'Foundation', 'Quartz', 'setproctitle', 'markdown'],
    'includes': ['settings', 'utils', 'display_utils', 'settings_window', 'summary_window', 'html.parser', 'xml.etree.ElementTree'],
}

setup(
    name='Sith',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
