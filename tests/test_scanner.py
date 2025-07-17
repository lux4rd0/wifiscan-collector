"""Tests for WiFi scanner module."""

from wifiscan_collector.scanner import WifiScanner

# Sample iw scan output
SAMPLE_OUTPUT = """BSS 00:11:22:33:44:55(on wlan0)
        TSF: 123456789 usec (1d, 10:17:36)
        freq: 2412
        beacon interval: 100 TUs
        capability: ESS Privacy ShortPreamble ShortSlotTime (0x0431)
        signal: -45.00 dBm
        last seen: 0 ms ago
        Information elements from Probe Response frame:
        SSID: TestNetwork
        DS Parameter set: channel 1
        HT capabilities:
                Capabilities: 0x11ed
BSS aa:bb:cc:dd:ee:ff(on wlan0)
        TSF: 987654321 usec (0d, 00:16:27)
        freq: 5180
        beacon interval: 100 TUs
        capability: ESS (0x0001)
        signal: -72.00 dBm
        SSID:
        DS Parameter set: channel 36
BSS 11:22:33:44:55:66(on wlan0)
        freq: 6155
        capability: ESS Privacy (0x0011)
        signal: -58.00 dBm
        SSID: WiFi6Network
        DS Parameter set: channel 41
        RSN:
                 Authentication suites: PSK SAE
        HE capabilities:
                HE MAC Capabilities (0x000c)
        Maximum TX power: 30 dBm
"""


class TestWifiScanner:
    """Test WiFi scanner functionality."""

    def test_parse_iw_output(self) -> None:
        """Test parsing of iw scan output."""
        scanner = WifiScanner("wlan0")
        networks = scanner._parse_iw_output(SAMPLE_OUTPUT)

        assert len(networks) == 3

        # Test first network (2.4GHz)
        assert networks[0].mac == "00:11:22:33:44:55"
        assert networks[0].essid == "TestNetwork"
        assert networks[0].frequency == "2412"
        assert networks[0].band == "2g"
        assert networks[0].channel == "1"
        assert networks[0].signal_level == -45
        assert networks[0].encryption == "on"
        assert networks[0].ht_capable is True

        # Test second network (5GHz, hidden)
        assert networks[1].mac == "aa:bb:cc:dd:ee:ff"
        assert networks[1].essid == "hidden"
        assert networks[1].frequency == "5180"
        assert networks[1].band == "5g"
        assert networks[1].channel == "36"
        assert networks[1].signal_level == -72
        assert networks[1].encryption == "off"

        # Test third network (6GHz, WiFi 6)
        assert networks[2].mac == "11:22:33:44:55:66"
        assert networks[2].essid == "WiFi6Network"
        assert networks[2].frequency == "6155"
        assert networks[2].band == "6g"
        assert networks[2].channel == "41"
        assert networks[2].signal_level == -58
        assert networks[2].encryption == "on"
        assert networks[2].he_capable is True
        assert networks[2].wpa3 is True
        assert networks[2].max_tx_power == 30

    def test_infer_band(self) -> None:
        """Test WiFi band inference."""
        assert WifiScanner.infer_band(2412) == "2g"
        assert WifiScanner.infer_band(2484) == "2g"
        assert WifiScanner.infer_band(5180) == "5g"
        assert WifiScanner.infer_band(5825) == "5g"
        assert WifiScanner.infer_band(5945) == "6g"
        assert WifiScanner.infer_band(7095) == "6g"
        assert WifiScanner.infer_band(900) == "unknown"
        assert WifiScanner.infer_band(8000) == "unknown"

    def test_empty_output(self) -> None:
        """Test parsing empty output."""
        scanner = WifiScanner("wlan0")
        networks = scanner._parse_iw_output("")
        assert networks == []

    def test_malformed_output(self) -> None:
        """Test parsing malformed output."""
        scanner = WifiScanner("wlan0")
        malformed = "This is not valid iw output\nRandom text\n"
        networks = scanner._parse_iw_output(malformed)
        assert networks == []

    def test_select_best_interface(self) -> None:
        """Test interface selection logic."""
        # Test with wlan0 UP
        interfaces = [
            ("wlan0", "administratively UP, operationally DOWN"),
            ("wlp3s0", "DOWN"),
            ("wlx1234", "DOWN"),
        ]
        assert WifiScanner.select_best_interface(interfaces) == "wlan0"

        # Test with no preferred interface UP
        interfaces = [
            ("wlp3s0", "administratively UP, operationally DOWN"),
            ("wlx1234", "DOWN"),
        ]
        assert WifiScanner.select_best_interface(interfaces) == "wlp3s0"

        # Test with only non-preferred interface
        interfaces = [("eth0", "administratively UP, operationally UP")]
        assert WifiScanner.select_best_interface(interfaces) == "eth0"

        # Test with empty list
        assert WifiScanner.select_best_interface([]) is None
