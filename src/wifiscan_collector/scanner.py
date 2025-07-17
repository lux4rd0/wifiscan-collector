"""WiFi scanner module.

This module provides WiFi network scanning capabilities using the Linux `iw` tool.
It supports modern WiFi standards including WiFi 6/6E and provides comprehensive
network information including capabilities, security, and signal strength.

The module includes:
- WiFi network scanning using iw command
- Network information parsing and validation
- Interface discovery and selection
- Support for all WiFi bands (2.4GHz, 5GHz, 6GHz)
- Modern capability detection (HT, VHT, HE)
- Security information parsing (WPA3, encryption types)

Example:
    Basic scanning:
        scanner = WifiScanner("wlan0")
        networks = await scanner.scan()

    Auto interface discovery:
        interfaces = await WifiScanner.discover_wireless_interfaces()
        best_interface = WifiScanner.select_best_interface(interfaces)
        scanner = WifiScanner(best_interface)
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from .models import WifiNetwork

logger = logging.getLogger(__name__)


class WifiScanner:
    """WiFi network scanner using Linux iw command.

    This class provides comprehensive WiFi network scanning capabilities
    including interface management, network discovery, and data parsing.

    Features:
    - Async WiFi scanning using iw command
    - Interface validation and status checking
    - Comprehensive network information parsing
    - Support for WiFi 6/6E and modern standards
    - Security and capability detection
    - Band and channel analysis

    The scanner supports all modern WiFi standards and provides detailed
    information about nearby networks including signal strength, encryption,
    channel width, and wireless capabilities.

    Example:
        scanner = WifiScanner("wlan0", scan_timeout=30)

        # Check interface is ready
        if await scanner.check_interface():
            networks = await scanner.scan()
            for network in networks:
                print(f"{network.essid}: {network.signal_level}dBm")
    """

    @staticmethod
    def select_best_interface(interfaces: list[tuple[str, str]]) -> str | None:
        """Select the best wireless interface based on preferences.

        Preference order:
        1. Interfaces that are administratively UP
        2. Common interface names: wlan0, wlan1, wlp*, wlx*
        3. First available interface

        Args:
            interfaces: List of (interface_name, state) tuples

        Returns:
            Selected interface name or None if no interfaces available
        """
        if not interfaces:
            return None

        # Separate interfaces by admin state
        up_interfaces = []
        down_interfaces = []

        for iface, state in interfaces:
            if "admin UP" in state:
                up_interfaces.append(iface)
            else:
                down_interfaces.append(iface)

        # Define preference order for interface names
        preference_order = [
            "wlan0",  # Most common on Raspberry Pi and embedded systems
            "wlan1",  # Secondary wireless
            "wlp",  # PCI wireless (prefix match)
            "wlx",  # USB wireless (prefix match)
        ]

        # Check UP interfaces first
        for pref in preference_order:
            for iface in up_interfaces:
                if iface == pref or (len(pref) == 3 and iface.startswith(pref)):
                    logger.info(
                        f"Selected interface {iface} " f"(admin UP, matches preference)"
                    )
                    return iface

        # Then check DOWN interfaces
        for pref in preference_order:
            for iface in down_interfaces:
                if iface == pref or (len(pref) == 3 and iface.startswith(pref)):
                    logger.info(
                        f"Selected interface {iface} "
                        f"(matches preference, but admin DOWN)"
                    )
                    return iface

        # If no preferred interface found, use first UP interface
        if up_interfaces:
            logger.info(
                f"Selected interface {up_interfaces[0]} " f"(first admin UP interface)"
            )
            return up_interfaces[0]

        # Finally, use first available interface
        if interfaces:
            logger.info(
                f"Selected interface {interfaces[0][0]} "
                f"(first available, but admin DOWN)"
            )
            return interfaces[0][0]

        return None

    @staticmethod
    async def discover_wireless_interfaces() -> list[tuple[str, str]]:
        """Discover available wireless interfaces.

        Returns:
            List of tuples (interface_name, state) for wireless interfaces
        """
        interfaces = []
        try:
            # First, get all network interfaces
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "link",
                "show",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                # Parse interface names from ip link output
                lines = stdout.decode("utf-8").strip().split("\n")
                for i in range(0, len(lines), 2):  # Every other line has interface info
                    if ":" in lines[i]:
                        parts = lines[i].split(":")
                        if len(parts) >= 2:
                            iface_name = parts[1].strip()
                            # Check if it's a wireless interface in /sys/class/net
                            wireless_path = Path(
                                f"/sys/class/net/{iface_name}/wireless"
                            )
                            if wireless_path.exists():
                                # Extract state from the next line
                                state = "unknown"
                                if i + 1 < len(lines):
                                    if "state UP" in lines[i + 1]:
                                        state = "UP"
                                    elif "state DOWN" in lines[i + 1]:
                                        state = "DOWN"
                                    # Check for UP flag in the interface flags
                                    flags = lines[i].split("<")[1].split(">")[0]
                                    if "<" in lines[i] and "UP" in flags:
                                        state = f"admin UP, operationally {state}"
                                interfaces.append((iface_name, state))

        except Exception as e:
            logger.error(f"Error discovering wireless interfaces: {e}")

        return interfaces

    @staticmethod
    async def get_interface_details(interface: str) -> dict[str, Any] | None:
        """Get detailed information about a wireless interface.

        Args:
            interface: Interface name

        Returns:
            Dictionary with interface details or None if not found
        """
        try:
            details = {"name": interface}

            # Get basic interface info
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "link",
                "show",
                interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode("utf-8")
                # Extract MAC address
                mac_match = re.search(r"link/ether\s+([0-9a-fA-F:]+)", output)
                if mac_match:
                    details["mac"] = mac_match.group(1)

                # Extract state
                if "state UP" in output:
                    details["state"] = "UP"
                elif "state DOWN" in output:
                    details["state"] = "DOWN"
                else:
                    details["state"] = "unknown"

                # Check administrative state
                if "<" in output and "UP" in output.split("<")[1].split(">")[0]:
                    details["admin_state"] = "UP"
                else:
                    details["admin_state"] = "DOWN"

            # Get wireless capabilities
            proc = await asyncio.create_subprocess_exec(
                "iw",
                "dev",
                interface,
                "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode("utf-8")
                # Extract wireless info
                if "type" in output:
                    type_match = re.search(r"type\s+(\w+)", output)
                    if type_match:
                        details["type"] = type_match.group(1)

                if "channel" in output:
                    channel_match = re.search(r"channel\s+(\d+)", output)
                    if channel_match:
                        details["channel"] = channel_match.group(1)

                if "ssid" in output:
                    ssid_match = re.search(r"ssid\s+(.+)", output)
                    if ssid_match:
                        details["ssid"] = ssid_match.group(1).strip()

            return details

        except Exception as e:
            logger.error(f"Error getting interface details for {interface}: {e}")
            return None

    def __init__(self, interface: str, scan_timeout: int = 30):
        """Initialize WiFi scanner for specified interface.

        Args:
            interface: Wireless interface name (e.g., "wlan0", "wlp3s0")
            scan_timeout: Timeout for scan command in seconds (default: 30)

        Example:
            scanner = WifiScanner("wlan0")
            scanner = WifiScanner("wlp3s0", scan_timeout=60)
        """
        self.interface = interface
        self.scan_timeout = scan_timeout

    async def check_interface(self) -> bool:
        """Check if the wireless interface exists and is up."""
        try:
            # Run ip command asynchronously
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "link",
                "show",
                self.interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(
                    f"Interface {self.interface} not found. "
                    "Please check your WIFISCAN_COLLECTOR_WIRELESS_INTERFACE setting."
                )
                return False

            # Check if interface is administratively up (has UP flag)
            stdout_text = stdout.decode("utf-8")
            # Look for UP in the flags like <BROADCAST,MULTICAST,UP>
            flags = (
                stdout_text.split("<")[1].split(">")[0] if "<" in stdout_text else ""
            )
            if "<" in stdout_text and "UP" not in flags:
                logger.warning(
                    f"Interface {self.interface} is not UP. "
                    f"You may need to run: sudo ip link set {self.interface} up"
                )
                return False

            # For WiFi scanning, we only need the interface to be administratively UP
            # It doesn't need to be connected (state UP), just enabled
            logger.debug(f"Interface {self.interface} is ready for scanning")

            return True

        except Exception as e:
            logger.error(f"Error checking interface: {e}")
            return False

    async def scan(self) -> list[WifiNetwork] | None:
        """Run WiFi scan and return parsed networks."""
        try:
            # Run iw scan command asynchronously
            proc = await asyncio.create_subprocess_exec(
                "iw",
                "dev",
                self.interface,
                "scan",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.scan_timeout
                )
            except TimeoutError:
                proc.kill()
                await proc.wait()
                logger.error(f"Scan timed out after {self.scan_timeout} seconds")
                return None

            if proc.returncode != 0:
                logger.error(
                    f"iw scan failed with return code {proc.returncode}: "
                    f"{stderr.decode('utf-8')}"
                )
                return None

            # Parse the output
            networks = self._parse_iw_output(stdout.decode("utf-8"))

            if not networks:
                logger.warning("No networks found in scan")
            else:
                logger.debug(f"Found {len(networks)} networks")

            return networks

        except FileNotFoundError:
            logger.error("iw command not found. Please ensure 'iw' is installed.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during scan: {e}", exc_info=True)
            return None

    @staticmethod
    def infer_band(frequency: float) -> str:
        """Infer WiFi band based on frequency in MHz."""
        if 2400 <= frequency < 2500:
            return "2g"
        elif 4900 <= frequency < 5900:
            return "5g"
        elif 5900 <= frequency < 7100:
            return "6g"
        else:
            return "unknown"

    def _parse_iw_output(self, output: str) -> list[WifiNetwork]:
        """Parse the output from the 'iw' scan command."""
        networks: list[WifiNetwork] = []
        current_data: dict[str, Any] = {}

        for line in output.splitlines():
            line = line.strip()

            # Start of a new BSS section
            if line.startswith("BSS"):
                if current_data:
                    network = self._create_network_from_data(current_data)
                    networks.append(network)
                    logger.debug(f"Parsed network: {network}")

                current_data = {}

                mac_match = re.search(r"BSS ([0-9a-f:]+)", line, re.IGNORECASE)
                if mac_match:
                    current_data["mac"] = mac_match.group(1).lower()

            elif "freq:" in line:
                freq_match = re.search(r"freq: (\d+)", line)
                if freq_match:
                    frequency = freq_match.group(1)
                    current_data["frequency"] = frequency
                    current_data["band"] = self.infer_band(float(frequency))

            elif "signal:" in line:
                signal_match = re.search(r"signal: (-?\d+\.\d+)", line)
                if signal_match:
                    # Convert dBm to integer
                    current_data["signal_level"] = int(float(signal_match.group(1)))

            elif "SSID:" in line:
                ssid_match = re.search(r"SSID: (.+)", line)
                if ssid_match:
                    current_data["essid"] = ssid_match.group(1)

            elif "DS Parameter set: channel" in line:
                channel_match = re.search(r"channel (\d+)", line)
                if channel_match:
                    current_data["channel"] = channel_match.group(1)

            elif "capability:" in line:
                if "Privacy" in line:
                    current_data["encryption"] = "on"
                else:
                    current_data.setdefault("encryption", "off")

            # Parse HT capabilities (802.11n)
            elif "HT capabilities:" in line:
                current_data["ht_capable"] = True

            # Parse VHT capabilities (802.11ac)
            elif "VHT capabilities:" in line:
                current_data["vht_capable"] = True

            # Parse HE capabilities (802.11ax - WiFi 6)
            elif "HE capabilities:" in line:
                current_data["he_capable"] = True

            # Parse RSN (Robust Security Network) for WPA2/WPA3
            elif "RSN:" in line:
                # Check for WPA3 indicators in subsequent lines
                current_data["rsn_found"] = True

            # Look for SAE (WPA3) authentication
            elif "Authentication suites:" in line and current_data.get("rsn_found"):
                if "SAE" in line or "OWE" in line:
                    current_data["wpa3"] = True

            # Parse channel width from HT/VHT operation
            elif "HT operation:" in line or "VHT operation:" in line:
                # Extract channel width info
                if "secondary channel offset:" in line:
                    if "above" in line or "below" in line:
                        current_data.setdefault("channel_width", "40")
                elif "Channel Width:" in line:
                    if "80 MHz" in line:
                        current_data["channel_width"] = "80"
                    elif "160 MHz" in line:
                        current_data["channel_width"] = "160"
                    elif "80+80 MHz" in line:
                        current_data["channel_width"] = "80+80"

            # Parse maximum TX power
            elif "Maximum TX power:" in line:
                tx_power_match = re.search(r"Maximum TX power: (-?\d+)", line)
                if tx_power_match:
                    current_data["max_tx_power"] = int(tx_power_match.group(1))

        # Don't forget the last network
        if current_data:
            network = self._create_network_from_data(current_data)
            networks.append(network)
            logger.debug(f"Parsed network: {network}")

        return networks

    @staticmethod
    def _create_network_from_data(data: dict[str, Any]) -> WifiNetwork:
        """Create a WifiNetwork object from parsed data."""
        return WifiNetwork(
            mac=data.get("mac", "unknown"),
            essid=data.get("essid", "hidden"),
            frequency=data.get("frequency"),
            band=data.get("band"),
            channel=data.get("channel"),
            signal_level=data.get("signal_level"),
            encryption=data.get("encryption"),
            he_capable=data.get("he_capable", False),
            vht_capable=data.get("vht_capable", False),
            ht_capable=data.get("ht_capable", False),
            wpa3=data.get("wpa3", False),
            channel_width=data.get("channel_width"),
            max_tx_power=data.get("max_tx_power"),
        )
