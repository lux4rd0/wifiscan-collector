"""Utility functions for WiFi Scanner.

This module provides utility functions for secure logging and configuration
handling, particularly for obfuscating sensitive information.

Example:
    Obfuscating sensitive values:
        safe_token = obfuscate_value("influxdb_token", "secret123456789")
        # Returns: "secr...6789"

    Getting safe configuration:
        config = Config()
        safe_config = get_safe_config_dict(config)
        # Returns dict with tokens obfuscated
"""

from typing import Any


def obfuscate_value(key: str, value: str) -> str:
    """Obfuscate sensitive values for secure logging.

    This function checks if a configuration key contains sensitive information
    (like tokens, passwords, secrets) and obfuscates the value to prevent
    accidental exposure in logs while still showing enough information
    to verify the configuration is set.

    Args:
        key: The configuration key name to check for sensitivity
        value: The value to potentially obfuscate

    Returns:
        Obfuscated value if key is sensitive, original value otherwise

    Example:
        obfuscate_value("influxdb_token", "secret123456789")
        # Returns: "secr...6789"

        obfuscate_value("scan_interval", "30")
        # Returns: "30" (not sensitive)

        obfuscate_value("password", "short")
        # Returns: "<5 chars>" (too short to show partial)
    """
    # List of keys that contain sensitive data
    sensitive_keys = {"token", "password", "secret", "key", "auth"}

    # Check if the key contains any sensitive words
    key_lower = key.lower()
    if any(sensitive in key_lower for sensitive in sensitive_keys):
        if len(value) > 8:
            # Show first 4 and last 4 characters
            return f"{value[:4]}...{value[-4:]}"
        else:
            # For short values, just show length
            return f"<{len(value)} chars>"

    return value


def get_safe_config_dict(config: Any) -> dict[str, str]:
    """Get configuration as dictionary with sensitive values obfuscated.

    Takes a Pydantic configuration object and returns a dictionary
    representation with all sensitive values (tokens, passwords, etc.)
    obfuscated for safe logging.

    Args:
        config: Pydantic config object with model_dump() method

    Returns:
        Dictionary with string values, sensitive data obfuscated

    Example:
        config = Config()
        safe_config = get_safe_config_dict(config)

        # Original config might have:
        # {"influxdb_token": "secret123456789", "scan_interval": 30}

        # Safe config returns:
        # {"influxdb_token": "secr...6789", "scan_interval": "30"}
    """
    result = {}

    # Get all fields from the Pydantic model
    for field_name, field_value in config.model_dump().items():
        if field_value is not None:
            str_value = str(field_value)
            safe_value = obfuscate_value(field_name, str_value)
            result[field_name] = safe_value

    return result
