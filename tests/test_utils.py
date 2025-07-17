"""Tests for utility functions."""

from wifiscan_collector.config import Config
from wifiscan_collector.utils import get_safe_config_dict, obfuscate_value


class TestObfuscation:
    """Test value obfuscation."""

    def test_obfuscate_sensitive_values(self) -> None:
        """Test obfuscation of sensitive values."""
        # Long token
        assert obfuscate_value("influxdb_token", "abcdefghijklmnop") == "abcd...mnop"

        # Short token
        assert obfuscate_value("api_key", "abc123") == "<6 chars>"

        # Password
        assert obfuscate_value("password", "mysecretpassword") == "myse...word"

        # Auth header
        assert obfuscate_value("auth_header", "Bearer token123") == "Bear...n123"

    def test_non_sensitive_values(self) -> None:
        """Test that non-sensitive values are not obfuscated."""
        assert (
            obfuscate_value("influxdb_url", "http://localhost:8086")
            == "http://localhost:8086"
        )
        assert obfuscate_value("wireless_interface", "wlan0") == "wlan0"
        assert obfuscate_value("scan_interval", "5") == "5"
        assert obfuscate_value("log_level", "INFO") == "INFO"

    def test_get_safe_config_dict(self) -> None:
        """Test getting safe config dictionary."""
        config = Config()
        safe_dict = get_safe_config_dict(config)

        # Check that token is obfuscated
        assert safe_dict["influxdb_token"] != config.influxdb_token
        assert "..." in safe_dict["influxdb_token"]

        # Check that non-sensitive values are unchanged
        assert safe_dict["influxdb_url"] == config.influxdb_url
        if config.wireless_interface:
            assert safe_dict["wireless_interface"] == config.wireless_interface
        assert safe_dict["scan_interval"] == str(config.scan_interval)
