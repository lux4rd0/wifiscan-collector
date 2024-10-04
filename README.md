# WiFiScan Collector

The **WiFiScan Collector** is a Python-based tool that scans available Wi-Fi networks using the `iw` tool, parses the scan results, and sends structured data to an InfluxDB database for storage and analysis. This tool provides insights into nearby wireless networks, including signal strength, frequency band, channel, and other essential Wi-Fi parameters.

## Features

- **Wi-Fi Scanning with `iw`:** Collects data about nearby Wi-Fi networks such as SSID, MAC address, channel, signal strength, encryption type, and frequency band (2.4GHz, 5GHz, or 6GHz).
- **Data Storage with InfluxDB:** Sends collected network data to an InfluxDB instance for monitoring, visualization, or further analysis.
- **Configurable Environment:** Configurable through environment variables for setting scan intervals, logging levels, and InfluxDB connection details.
- **Retry Logic:** Automatically retries scans in case of transient errors or missing network data.

## Environment Variables

You can configure the collector using the following environment variables:

- **`WIFISCAN_COLLECTOR_INFLUXDB_URL`**: URL of the InfluxDB instance (e.g., `http://influxdb:8086`).
- **`WIFISCAN_COLLECTOR_INFLUXDB_TOKEN`**: Authentication token for InfluxDB.
- **`WIFISCAN_COLLECTOR_INFLUXDB_ORG`**: InfluxDB organization name.
- **`WIFISCAN_COLLECTOR_INFLUXDB_BUCKET`**: InfluxDB bucket name to store Wi-Fi scan results.
- **`WIFISCAN_COLLECTOR_SCAN_INTERVAL`**: Interval (in seconds) between Wi-Fi scans.
- **`WIFISCAN_COLLECTOR_LOG_LEVEL`**: Logging level (e.g., `DEBUG`, `INFO`, `ERROR`).

## How to Run

### Run the Collector with Docker

To simplify deployment, you can run the WiFiScan Collector using Docker.

### Steps to run the collector:

1. **Create a `docker-compose.yaml` file:**

   Example `compose.yaml`:

   ```yaml
   services:
     wifiscan-collector:
       image: wifiscan-collector:latest
       container_name: wifiscan-collector
       environment:
         - WIFISCAN_COLLECTOR_INFLUXDB_URL=http://influxdb:8086
         - WIFISCAN_COLLECTOR_INFLUXDB_TOKEN=your-token-here
         - WIFISCAN_COLLECTOR_INFLUXDB_ORG=your-org
         - WIFISCAN_COLLECTOR_INFLUXDB_BUCKET=wifiscan
         - WIFISCAN_COLLECTOR_SCAN_INTERVAL=10
         - WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG
       network_mode: host  # To give the container access to the host Wi-Fi interfaces
       restart: unless-stopped
   ```

4. **Run the container using Docker Compose:**

   ```bash
   docker compose up
   ```

This will start the `wifiscan-collector` container, which will scan nearby Wi-Fi networks using the `iw` command, parse the results, and send the data to InfluxDB at the specified interval.
