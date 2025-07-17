"""Data models for WiFi Scanner.

This module contains data classes for representing WiFi network information
and converting it to InfluxDB format for storage.

Example:
    Creating a WiFi network:
        network = WifiNetwork(
            mac="00:11:22:33:44:55",
            essid="MyNetwork",
            frequency="2412",
            band="2g",
            channel="1",
            signal_level=-45,
            encryption="on",
            he_capable=True
        )

    Converting to InfluxDB point:
        point = network.to_influxdb_point()
"""

from dataclasses import dataclass

from influxdb_client import Point


@dataclass
class WifiNetwork:
    """Represents a detected WiFi network.

    This class stores all the information about a WiFi network detected
    during scanning, including signal strength, capabilities, and security
    information.

    Attributes:
        mac: MAC address of the access point (required)
        essid: Network name (SSID) or "hidden" for hidden networks
        frequency: Frequency in MHz (e.g., "2412", "5180")
        band: Frequency band ("2g", "5g", "6g", "unknown")
        channel: Channel number (e.g., "1", "36", "149")
        signal_level: Signal strength in dBm (negative values)
        encryption: Encryption status ("on", "off")
        he_capable: WiFi 6 (802.11ax) High Efficiency support
        vht_capable: WiFi 5 (802.11ac) Very High Throughput support
        ht_capable: WiFi 4 (802.11n) High Throughput support
        wpa3: WPA3 security support
        channel_width: Channel width in MHz ("20", "40", "80", "160")
        max_tx_power: Maximum transmit power in dBm

    Example:
        Basic network:
            network = WifiNetwork(mac="00:11:22:33:44:55")

        Full network information:
            network = WifiNetwork(
                mac="00:11:22:33:44:55",
                essid="MyNetwork",
                frequency="2412",
                band="2g",
                channel="1",
                signal_level=-45,
                encryption="on",
                he_capable=True,
                channel_width="80"
            )
    """

    mac: str
    essid: str = "hidden"
    frequency: str | None = None
    band: str | None = None
    channel: str | None = None
    signal_level: int | None = None
    encryption: str | None = None
    he_capable: bool = False  # High Efficiency (802.11ax)
    vht_capable: bool = False  # Very High Throughput (802.11ac)
    ht_capable: bool = False  # High Throughput (802.11n)
    wpa3: bool = False  # WPA3 security
    channel_width: str | None = None  # 20, 40, 80, 160 MHz
    max_tx_power: int | None = None  # Maximum transmit power in dBm

    def to_influxdb_point(self) -> Point:
        """Convert WiFi network to InfluxDB point for storage.

        Creates an InfluxDB point with the measurement name "wifi_scan"
        and populates it with tags and fields from the network data.

        Tags (indexed, used for querying):
            - mac, essid, frequency, band, channel, encryption
            - channel_width, he_capable, vht_capable, ht_capable, wpa3

        Fields (not indexed, used for values):
            - signal_level, max_tx_power
            - present (added when no other fields available)

        Returns:
            InfluxDB Point object ready for writing

        Example:
            network = WifiNetwork(mac="00:11:22:33:44:55", signal_level=-45)
            point = network.to_influxdb_point()
            # Creates point with mac tag and signal_level field
        """
        point = Point("wifi_scan").tag("mac", self.mac).tag("essid", self.essid)

        if self.frequency:
            point = point.tag("frequency", self.frequency)

        if self.band:
            point = point.tag("band", self.band)

        if self.channel:
            point = point.tag("channel", self.channel)

        if self.encryption:
            point = point.tag("encryption", self.encryption)

        if self.channel_width:
            point = point.tag("channel_width", self.channel_width)

        # Add capability tags
        point = point.tag("he_capable", str(self.he_capable))
        point = point.tag("vht_capable", str(self.vht_capable))
        point = point.tag("ht_capable", str(self.ht_capable))
        point = point.tag("wpa3", str(self.wpa3))

        # Add fields
        if self.signal_level is not None:
            point = point.field("signal_level", self.signal_level)

        if self.max_tx_power is not None:
            point = point.field("max_tx_power", self.max_tx_power)

        # InfluxDB requires at least one field - add presence indicator
        # if no other fields are present
        if self.signal_level is None and self.max_tx_power is None:
            point = point.field("present", 1)

        return point  # type: ignore[no-any-return]
