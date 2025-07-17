"""Pytest configuration and fixtures."""

import pytest
from pytest import MonkeyPatch


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch: MonkeyPatch) -> None:
    """Set up test environment variables."""
    monkeypatch.setenv("WIFISCAN_COLLECTOR_INFLUXDB_TOKEN", "test-token")
    monkeypatch.setenv("WIFISCAN_COLLECTOR_INFLUXDB_ORG", "test-org")
    monkeypatch.setenv("WIFISCAN_COLLECTOR_INFLUXDB_URL", "http://localhost:8086")
    monkeypatch.setenv("WIFISCAN_COLLECTOR_LOG_LEVEL", "DEBUG")
