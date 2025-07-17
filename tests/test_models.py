"""Tests for data models."""

from wifiscan_collector.models import WifiNetwork


class TestWifiNetwork:
    """Test WifiNetwork model."""

    def test_default_values(self) -> None:
        """Test default values for WifiNetwork."""
        network = WifiNetwork(mac="aa:bb:cc:dd:ee:ff")

        assert network.mac == "aa:bb:cc:dd:ee:ff"
        assert network.essid == "hidden"
        assert network.frequency is None
        assert network.band is None
        assert network.channel is None
        assert network.signal_level is None
        assert network.encryption is None
        assert network.he_capable is False
        assert network.vht_capable is False
        assert network.ht_capable is False
        assert network.wpa3 is False
        assert network.channel_width is None
        assert network.max_tx_power is None

    def test_full_network(self) -> None:
        """Test WifiNetwork with all fields."""
        network = WifiNetwork(
            mac="00:11:22:33:44:55",
            essid="TestNetwork",
            frequency="2412",
            band="2g",
            channel="1",
            signal_level=-45,
            encryption="on",
            he_capable=True,
            vht_capable=True,
            ht_capable=True,
            wpa3=True,
            channel_width="80",
            max_tx_power=30,
        )

        assert network.essid == "TestNetwork"
        assert network.he_capable is True
        assert network.channel_width == "80"

    def test_to_influxdb_point(self) -> None:
        """Test conversion to InfluxDB point."""
        network = WifiNetwork(
            mac="00:11:22:33:44:55",
            essid="TestNetwork",
            frequency="2412",
            band="2g",
            channel="1",
            signal_level=-45,
            encryption="on",
        )

        point = network.to_influxdb_point()
        line_protocol = point.to_line_protocol()

        # Check that essential fields are in the line protocol
        assert "wifi_scan" in line_protocol
        assert "mac=00:11:22:33:44:55" in line_protocol
        assert "essid=TestNetwork" in line_protocol
        assert "band=2g" in line_protocol
        assert "signal_level=-45i" in line_protocol

    def test_to_influxdb_point_minimal(self) -> None:
        """Test conversion to InfluxDB point with minimal data."""
        network = WifiNetwork(mac="aa:bb:cc:dd:ee:ff")

        point = network.to_influxdb_point()
        line_protocol = point.to_line_protocol()

        # Check that essential fields are in the line protocol
        assert "wifi_scan" in line_protocol
        assert "mac=aa:bb:cc:dd:ee:ff" in line_protocol
        assert "essid=hidden" in line_protocol
        # Should have presence field since no signal data
        assert "present=1i" in line_protocol
