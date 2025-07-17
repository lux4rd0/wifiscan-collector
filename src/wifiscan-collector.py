#!/usr/bin/env python3
"""WiFi Scanner Collector entry point.

This is the main entry point for the WiFi Scanner Collector application.
It provides a simple command-line interface to start the scanning service.

The application will:
1. Load configuration from environment variables
2. Discover and validate wireless interfaces
3. Connect to InfluxDB
4. Start continuous WiFi scanning
5. Handle graceful shutdown on SIGTERM/SIGINT

Usage:
    python src/wifiscan-collector.py

    Or make it executable:
    chmod +x src/wifiscan-collector.py
    ./src/wifiscan-collector.py

Environment variables:
    WIFISCAN_COLLECTOR_INFLUXDB_TOKEN: InfluxDB authentication token (required)
    WIFISCAN_COLLECTOR_INFLUXDB_ORG: InfluxDB organization (required)
    WIFISCAN_COLLECTOR_INFLUXDB_URL: InfluxDB URL (default: http://localhost:8086)
    WIFISCAN_COLLECTOR_WIRELESS_INTERFACE: Interface name (default: auto-detect)
    WIFISCAN_COLLECTOR_SCAN_INTERVAL: Scan interval in seconds (default: 5)
    WIFISCAN_COLLECTOR_LOG_LEVEL: Logging level (default: INFO)

For complete configuration options, see the documentation.
"""

from wifiscan_collector.main import run

if __name__ == "__main__":
    run()
