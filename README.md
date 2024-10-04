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

## Requirements

- Docker
- InfluxDB 2.x instance

## Running WiFiScan Collector with Docker

### Step 1: Create the `docker-compose.yaml`

Here is the `docker-compose.yaml` file you can use to run WiFiScan Collector:

```yaml
name: wifiscan-collector
services:
  wifiscan-collector:
    cap_add:
      - NET_ADMIN
    container_name: wifiscan-collector
    environment:
      TZ: America/Chicago
      WIFISCAN_COLLECTOR_INFLUXDB_BUCKET: wifiscan
      WIFISCAN_COLLECTOR_INFLUXDB_ORG: Lux4rd0
      WIFISCAN_COLLECTOR_INFLUXDB_TOKEN: <token>
      WIFISCAN_COLLECTOR_INFLUXDB_URL: http://influxdb:8086
      WIFISCAN_COLLECTOR_LOG_LEVEL: INFO
      WIFISCAN_COLLECTOR_MAX_RETRIES: "3"
      WIFISCAN_COLLECTOR_RETRY_DELAY: "2"
      WIFISCAN_COLLECTOR_SCAN_INTERVAL: "10"
    image: lux4rd0/wifiscan-collector:latest
    network_mode: host
    restart: unless-stopped
```

### Step 2: Start WiFiScan Collector

To start the WiFiScan Collector service using Docker Compose, follow these steps:

1. Save the `compose.yaml` file in your project directory.
2. Run the following command in the directory where the `compose.yaml` file is located:

   ```bash
   docker-compose up -d
   ```

This command will start the WiFiScan Collector service in the background. It will continuously scan for Wi-Fi networks and send the data to your specified InfluxDB instance.

### Step 3: Troubleshooting

If you encounter issues such as the `wlan0` interface being down, you can troubleshoot with the following commands:

1. **Check the status of your wireless interface:**

   ```bash
   ifconfig wlan0 up
   ```

2. **Bring up the interface manually:**

   ```bash
   sudo ip link set wlan0 up
   ```
