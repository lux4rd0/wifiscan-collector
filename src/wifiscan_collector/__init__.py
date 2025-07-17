"""WiFi Scanner Collector package.

This package provides a modern, async WiFi network scanner that collects
comprehensive WiFi network information and stores it in InfluxDB.

Features:
    - Async WiFi scanning using Linux iw tool
    - InfluxDB integration with batch writing
    - Circuit breaker pattern for reliability
    - Auto interface detection
    - Production-ready error handling
"""

__version__ = "1.0.0"
