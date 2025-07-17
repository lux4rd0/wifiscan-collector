"""Tests for storage module."""

from unittest.mock import AsyncMock, patch

import pytest

from wifiscan_collector.config import Config
from wifiscan_collector.models import WifiNetwork
from wifiscan_collector.storage import CircuitState, InfluxDBStorage


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Config()
    config.max_buffer_size = 100
    config.circuit_breaker_threshold = 3
    config.circuit_breaker_timeout = 60
    config.batch_size = 10
    config.batch_interval = 5
    return config


@pytest.fixture
def mock_storage(mock_config):
    """Create storage instance with mocked InfluxDB client."""
    with patch("wifiscan_collector.storage.InfluxDBClientAsync"):
        storage = InfluxDBStorage(mock_config)
        storage._write_api = AsyncMock()
        return storage


class TestInfluxDBStorage:
    """Test InfluxDB storage functionality."""

    def test_initialization(self, mock_config):
        """Test storage initialization."""
        storage = InfluxDBStorage(mock_config)

        assert storage._circuit_state == CircuitState.CLOSED
        assert storage._consecutive_failures == 0
        assert storage._total_received == 0
        assert storage._total_written == 0
        assert storage._total_dropped == 0
        assert len(storage._batch) == 0

    @pytest.mark.asyncio
    async def test_add_networks(self, mock_storage):
        """Test adding networks to batch."""
        networks = [
            WifiNetwork(mac="00:11:22:33:44:55", essid="Test1"),
            WifiNetwork(mac="aa:bb:cc:dd:ee:ff", essid="Test2"),
        ]

        await mock_storage.add_networks(networks)

        assert len(mock_storage._batch) == 2
        assert mock_storage._total_received == 2

    @pytest.mark.asyncio
    async def test_buffer_overflow(self, mock_storage, mock_config):
        """Test buffer overflow protection."""
        # Disable auto-flush for this test
        mock_storage._circuit_state = CircuitState.CLOSED
        original_batch_size = mock_config.batch_size
        mock_config.batch_size = 200  # Prevent auto-flush

        # Fill buffer to capacity
        networks = [WifiNetwork(mac=f"00:11:22:33:44:{i:02x}") for i in range(150)]

        await mock_storage.add_networks(networks)

        # Should be capped at max_buffer_size (deque automatically drops oldest)
        assert len(mock_storage._batch) == mock_config.max_buffer_size
        assert mock_storage._total_dropped == 50  # 150 - 100

        # Restore original batch size
        mock_config.batch_size = original_batch_size

    @pytest.mark.asyncio
    async def test_circuit_breaker(self, mock_storage):
        """Test circuit breaker functionality."""
        # Simulate write failures
        mock_storage._write_api.write.side_effect = Exception("Connection failed")

        # Add some networks
        networks = [WifiNetwork(mac="00:11:22:33:44:55")]
        await mock_storage.add_networks(networks)

        # Try to flush multiple times
        for _ in range(4):
            await mock_storage._flush_batch()

        # Circuit should be open after threshold failures
        assert mock_storage._circuit_state == CircuitState.OPEN
        assert mock_storage._consecutive_failures >= 3

    @pytest.mark.asyncio
    async def test_health_check(self, mock_storage):
        """Test health check functionality."""
        # Add some networks
        networks = [WifiNetwork(mac=f"00:11:22:33:44:{i:02x}") for i in range(5)]
        await mock_storage.add_networks(networks)

        health = await mock_storage.health_check()

        assert health["status"] == "healthy"
        assert health["buffer_size"] == 5
        assert health["buffer_capacity"] == 100
        assert health["circuit_breaker"] == "closed"
        assert health["total_dropped"] == 0

    def test_sanitize_error(self, mock_storage, mock_config):
        """Test error message sanitization."""
        error_msg = (
            f"Failed to connect to {mock_config.influxdb_url} "
            f"with token {mock_config.influxdb_token}"
        )
        error = Exception(error_msg)

        sanitized = mock_storage._sanitize_error(error)

        assert mock_config.influxdb_token not in sanitized
        assert "***TOKEN***" in sanitized
        # URL should be sanitized to show only host
        assert "http://localhost:8086/..." in sanitized
