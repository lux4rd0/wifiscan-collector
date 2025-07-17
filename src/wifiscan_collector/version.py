"""Version information for WiFi Scanner Collector.

This module handles version detection from multiple sources including
environment variables, VERSION file, and directory structure.

The version is determined in this order:
1. WIFISCAN_COLLECTOR_VERSION environment variable
2. VERSION file in project root
3. Default fallback version

Example:
    Getting version information:
        from wifiscan_collector.version import get_version_info

        info = get_version_info()
        print(f"Version: {info['version']}")
        print(f"Built: {info['build_time']}")
"""

import os
from datetime import UTC, datetime
from pathlib import Path


def _get_version() -> str:
    """Get version from environment or VERSION file.

    Attempts to determine the application version from multiple sources
    in order of preference:
    1. WIFISCAN_COLLECTOR_VERSION environment variable (Docker builds)
    2. VERSION file in project root
    3. Default fallback version

    Returns:
        Version string in semantic versioning format

    Example:
        version = _get_version()
        # Returns: "2025.7.0" or "1.0.0"
    """
    # First check environment variable (set during Docker build)
    env_version = os.getenv("WIFISCAN_COLLECTOR_VERSION")
    if env_version:
        return env_version

    # Try to read from VERSION file
    version_file = Path(__file__).parent.parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()

    # Default fallback
    return "1.0.0"


__version__ = _get_version()
__build_time__ = os.getenv(
    "WIFISCAN_COLLECTOR_BUILD_TIME", datetime.now(UTC).isoformat()
)


def get_version_info() -> dict:
    """Get comprehensive version information.

    Returns a dictionary containing version and build time information
    suitable for logging and display purposes.

    Returns:
        Dictionary with version and build_time keys

    Example:
        info = get_version_info()
        # Returns: {
        #     "version": "2025.7.0",
        #     "build_time": "2025-07-17T12:34:56.789Z"
        # }
    """
    return {
        "version": __version__,
        "build_time": __build_time__,
    }
