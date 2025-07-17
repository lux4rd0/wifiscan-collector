# WiFiScan Collector

A Python 3.13 async tool that scans WiFi networks using `iw` and stores data in InfluxDB. Supports modern WiFi 6/6E networks with comprehensive network analysis and production-ready reliability features.

## Features

- **WiFi Scanning:** Collects SSID, signal strength, encryption, channel, band (2.4/5/6 GHz), and WiFi 6/6E capabilities
- **InfluxDB Integration:** Async batch writing with circuit breaker and retry logic for reliability
- **Auto Interface Detection:** Automatically finds and selects the best wireless interface
- **Production Ready:** Built for long-running deployments with comprehensive error handling

## Quick Start

### Requirements
- Docker with `NET_ADMIN` capability
- InfluxDB 2.x instance
- Linux system with wireless interface

### Configuration
Set these environment variables:
```bash
WIFISCAN_COLLECTOR_INFLUXDB_TOKEN=your-token-here
WIFISCAN_COLLECTOR_INFLUXDB_ORG=your-org
WIFISCAN_COLLECTOR_INFLUXDB_URL=http://influxdb:8086  # optional
```

See [docs/configuration.md](docs/configuration.md) for all configuration options.

## Installation

### Docker (Recommended)
```bash
# Create .env file with your settings
cp .env.example .env

# Run with Docker Compose
docker-compose up -d
```

### Docker Compose Example
```yaml
services:
  wifiscan-collector:
    image: lux4rd0/wifiscan-collector:latest
    cap_add:
      - NET_ADMIN
    network_mode: host
    env_file:
      - .env
    restart: unless-stopped
```

### Manual Installation
See [docs/development.md](docs/development.md) for Python installation instructions.

## Troubleshooting

**Common issues:**
- **Permission denied**: Ensure container has `NET_ADMIN` capability
- **Interface not found**: Use `ip link show` to verify interface name
- **InfluxDB connection**: Check token, organization, and URL

**Debug mode:**
```bash
export WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG
docker logs -f wifiscan-collector
```

See [docs/troubleshooting.md](docs/troubleshooting.md) for comprehensive troubleshooting.

## Documentation

- **[Configuration Guide](docs/configuration.md)** - Complete configuration reference and examples
- **[Development Guide](docs/development.md)** - Setup, testing, and contribution guidelines
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Detailed problem-solving procedures

## License

MIT License - see LICENSE file for details.