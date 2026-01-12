# -*- coding: utf-8 -*-
"""
ProducerOS Version Information

Centralized version management for the application.
"""

# Version info
VERSION = "1.0.0"
VERSION_NAME = "Initial Release"
BUILD_DATE = "2026-01-12"

# Application info
APP_NAME = "ProducerOS"
APP_DESCRIPTION = "Professional Sample Library Manager for Music Producers"

# Contact & Links
WEBSITE = "https://produceros.app"
SUPPORT_EMAIL = "support@produceros.app"
GITHUB_URL = "https://github.com/produceros/produceros"

# Copyright
COPYRIGHT_YEAR = "2026"
COPYRIGHT_HOLDER = "ProducerOS"
COPYRIGHT = f"Copyright {COPYRIGHT_YEAR} {COPYRIGHT_HOLDER}. All rights reserved."

# Update server (for future update checker)
UPDATE_URL = "https://produceros.app/api/version.json"


def get_version_string() -> str:
    """Return formatted version string."""
    return f"v{VERSION}"


def get_full_version_string() -> str:
    """Return full version string with name."""
    return f"v{VERSION} - {VERSION_NAME}"


def get_about_info() -> dict:
    """Return all info needed for About dialog."""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "version_name": VERSION_NAME,
        "description": APP_DESCRIPTION,
        "copyright": COPYRIGHT,
        "website": WEBSITE,
        "support_email": SUPPORT_EMAIL,
        "github": GITHUB_URL,
        "build_date": BUILD_DATE,
    }
