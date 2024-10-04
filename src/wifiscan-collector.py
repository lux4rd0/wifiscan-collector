import subprocess
import re
import time
import os
import logging
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Setup logging based on environment variable
log_level = os.getenv("WIFISCAN_COLLECTOR_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))


class WifiScan:
    def __init__(self):
        # InfluxDB connection details from environment variables
        self.influxdb_url = os.getenv(
            "WIFISCAN_COLLECTOR_INFLUXDB_URL", "http://localhost:8086"
        )
        self.influxdb_token = os.getenv("WIFISCAN_COLLECTOR_INFLUXDB_TOKEN", "")
        self.influxdb_org = os.getenv("WIFISCAN_COLLECTOR_INFLUXDB_ORG", "")
        self.influxdb_bucket = os.getenv(
            "WIFISCAN_COLLECTOR_INFLUXDB_BUCKET", "wifiscan"
        )

        # Set scan interval from environment variable
        self.scan_interval = int(os.getenv("WIFISCAN_COLLECTOR_SCAN_INTERVAL", 5))

    def parse_iw_output(self, output):
        """Parse the output from the 'iw' scan command."""
        networks = []
        current_network = {}

        for line in output.splitlines():
            line = line.strip()

            # Start of a new BSS section
            if line.startswith("BSS"):
                if current_network:
                    logging.debug(f"Parsed network: {current_network}")
                    networks.append(current_network)
                current_network = {}

                mac_match = re.search(r"BSS ([0-9a-f:]+)", line)
                if mac_match:
                    current_network["mac"] = mac_match.group(1)

            elif "freq:" in line:
                freq_match = re.search(r"freq: (\d+)", line)
                if freq_match:
                    frequency = freq_match.group(1)
                    current_network["frequency"] = frequency
                    current_network["band"] = self.infer_band(float(frequency))

            elif "signal:" in line:
                signal_match = re.search(r"signal: (-?\d+)", line)
                if signal_match:
                    current_network["signal_level"] = signal_match.group(1)

            elif "SSID:" in line:
                ssid_match = re.search(r"SSID: (.+)", line)
                if ssid_match:
                    current_network["essid"] = ssid_match.group(1)

            elif "DS Parameter set: channel" in line:
                channel_match = re.search(r"channel (\d+)", line)
                if channel_match:
                    current_network["channel"] = channel_match.group(1)

            elif "capability" in line and "Privacy" in line:
                current_network["encryption"] = "on"
            elif "capability" in line and "Privacy" not in line:
                current_network["encryption"] = "off"

        if current_network:
            logging.debug(f"Parsed network: {current_network}")
            networks.append(current_network)

        return networks

    def infer_band(self, frequency):
        """Infer WiFi band based on frequency."""
        if 2400 <= frequency < 2500:
            return "2g"
        elif 4900 <= frequency < 5900:
            return "5g"
        elif 5900 <= frequency < 7100:
            return "6g"
        else:
            return "unknown"

    def send_to_influxdb(self, networks):
        try:
            client = InfluxDBClient(
                url=self.influxdb_url, token=self.influxdb_token, org=self.influxdb_org
            )
            write_api = client.write_api(write_options=SYNCHRONOUS)

            for network in networks:
                point = (
                    Point("wifi_scan")
                    .tag("mac", network.get("mac", "unknown"))
                    .tag("essid", network.get("essid", "hidden"))
                    .tag("frequency", network.get("frequency", "unknown"))
                    .tag("band", network.get("band", "unknown"))
                    .tag("channel", network.get("channel", "unknown"))
                    .tag("encryption", network.get("encryption", "unknown"))
                    .field("signal_level", int(network.get("signal_level", "-100")))
                )

                write_api.write(bucket=self.influxdb_bucket, record=point)

            logging.info(f"Successfully sent {len(networks)} records to InfluxDB")
        except Exception as e:
            logging.error(f"Error sending data to InfluxDB: {e}")
        finally:
            client.close()

    def run_scan(self):
        try:
            start_time = time.time()

            # Run the iw command and capture the output
            result = subprocess.run(
                ["iw", "dev", "wlan0", "scan"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if result.returncode != 0:
                logging.error(f"iw scan failed: {result.stderr.decode('utf-8')}")
                return None, 0

            output = result.stdout.decode("utf-8")

            # Measure how long the scan took
            elapsed_time = time.time() - start_time
            logging.info(f"Scan completed in {elapsed_time:.2f} seconds")

            # Parse the iw output
            return self.parse_iw_output(output), elapsed_time

        except Exception as e:
            logging.error(f"Error running iw scan: {e}")
            return None, 0

    def start(self):
        retries = 0
        max_retries = 3

        while True:
            networks, elapsed_time = self.run_scan()

            if networks:
                retries = 0  # Reset retries after a successful scan
                self.send_to_influxdb(networks)
            else:
                retries += 1
                logging.error(f"Scan failed (attempt {retries})")
                if retries >= max_retries:
                    logging.error("Max retries reached, scan failed.")
                    retries = 0

            # Calculate how much time to sleep based on the scan time
            sleep_time = max(0, self.scan_interval - elapsed_time)

            if sleep_time > 0:
                logging.info(f"Sleeping for {sleep_time:.2f} seconds")
            else:
                logging.warning("Scan took longer than the interval, skipping sleep")

            time.sleep(sleep_time)


if __name__ == "__main__":
    # Instantiate the scanner
    scanner = WifiScan()
    scanner.start()
