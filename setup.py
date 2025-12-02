"""
Setup script for creating a standalone macOS .app bundle.
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,  # Add an .icns file here if you create one
    'plist': {
        'CFBundleName': 'Work Clock',
        'CFBundleDisplayName': 'Work Clock',
        'CFBundleIdentifier': 'com.khanh.workclock',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Makes it a menubar/background app (no dock icon)
        'NSHighResolutionCapable': True,
    },
    'packages': ['objc', 'Cocoa', 'Foundation', 'setproctitle'],
    'includes': ['settings', 'utils'],
}

setup(
    name='Work Clock',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
