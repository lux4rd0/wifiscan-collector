"""Tests for configuration module."""

from pytest import MonkeyPatch

from wifiscan_collector.config import Config


def test_config_from_env() -> None:
    """Test configuration loading from environment variables."""
    config = Config()

    assert config.influxdb_token == "test-token"
    assert config.influxdb_org == "test-org"
    assert config.influxdb_url == "http://localhost:8086"
    assert config.influxdb_bucket == "wifiscan"
    assert config.wireless_interface is None  # Now auto-detects by default
    assert config.scan_interval == 5
    assert config.batch_size == 100
    assert config.log_level == "DEBUG"

    # Test new config options
    assert config.max_buffer_size == 10000
    assert config.circuit_breaker_threshold == 5
    assert config.circuit_breaker_timeout == 300
    assert config.flush_on_scan is False
    assert config.status_log_interval == 300


def test_config_validation() -> None:
    """Test configuration validation."""
    config = Config()

    # Test valid log level
    assert config.log_level == "DEBUG"

    # Test positive integer validation
    assert config.scan_interval > 0
    assert config.batch_size > 0
    assert config.max_retries >= 0


def test_config_custom_values(monkeypatch: MonkeyPatch) -> None:
    """Test configuration with custom values."""
    monkeypatch.setenv("WIFISCAN_COLLECTOR_WIRELESS_INTERFACE", "wlan1")
    monkeypatch.setenv("WIFISCAN_COLLECTOR_SCAN_INTERVAL", "10")
    monkeypatch.setenv("WIFISCAN_COLLECTOR_BATCH_SIZE", "200")

    config = Config()

    assert config.wireless_interface == "wlan1"
    assert config.scan_interval == 10
    assert config.batch_size == 200
