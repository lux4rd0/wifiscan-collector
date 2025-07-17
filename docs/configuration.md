# Configuration Guide

This guide provides detailed information about configuring the WiFiScan Collector for different use cases and environments.

## Configuration Overview

The WiFiScan Collector uses environment variables with the `WIFISCAN_COLLECTOR_` prefix for all configuration. Configuration is validated using Pydantic models with automatic type conversion and validation.

## Environment Variables

### InfluxDB Configuration

#### Required Settings
- **`WIFISCAN_COLLECTOR_INFLUXDB_TOKEN`**: Authentication token for InfluxDB
  - **Required**: Yes
  - **Type**: String
  - **Example**: `your-influxdb-token-here`

- **`WIFISCAN_COLLECTOR_INFLUXDB_ORG`**: InfluxDB organization name
  - **Required**: Yes
  - **Type**: String
  - **Example**: `my-org`

#### Optional Settings
- **`WIFISCAN_COLLECTOR_INFLUXDB_URL`**: URL of the InfluxDB instance
  - **Default**: `http://localhost:8086`
  - **Type**: String
  - **Example**: `http://influxdb:8086`, `https://us-west-2-1.aws.cloud2.influxdata.com`

- **`WIFISCAN_COLLECTOR_INFLUXDB_BUCKET`**: InfluxDB bucket name
  - **Default**: `wifiscan`
  - **Type**: String
  - **Example**: `wifi-networks`, `sensors`

- **`WIFISCAN_COLLECTOR_INFLUXDB_TIMEOUT`**: Connection timeout in milliseconds
  - **Default**: `30000`
  - **Type**: Integer
  - **Range**: 1000-300000
  - **Example**: `60000` (1 minute)

### Batch Writing Configuration

- **`WIFISCAN_COLLECTOR_BATCH_SIZE`**: Points to batch before writing
  - **Default**: `100`
  - **Type**: Integer
  - **Range**: 1-10000
  - **Recommendation**: 50-500 for most use cases

- **`WIFISCAN_COLLECTOR_BATCH_INTERVAL`**: Maximum seconds before flushing
  - **Default**: `10`
  - **Type**: Integer
  - **Range**: 1-3600
  - **Recommendation**: 5-60 seconds

- **`WIFISCAN_COLLECTOR_BATCH_RETRY_INTERVAL`**: Retry interval for failed batches
  - **Default**: `5`
  - **Type**: Integer
  - **Range**: 1-300
  - **Note**: Uses exponential backoff

- **`WIFISCAN_COLLECTOR_FLUSH_ON_SCAN`**: Flush after each scan
  - **Default**: `false`
  - **Type**: Boolean
  - **Values**: `true`, `false`
  - **Use Case**: Enable for critical data collection

### Circuit Breaker Configuration

- **`WIFISCAN_COLLECTOR_MAX_BUFFER_SIZE`**: Maximum points in memory
  - **Default**: `10000`
  - **Type**: Integer
  - **Range**: 100-100000
  - **Memory**: ~500 bytes per point

- **`WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_THRESHOLD`**: Failures before opening circuit
  - **Default**: `5`
  - **Type**: Integer
  - **Range**: 1-50
  - **Recommendation**: 3-10

- **`WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_TIMEOUT`**: Seconds before testing circuit
  - **Default**: `300`
  - **Type**: Integer
  - **Range**: 30-3600
  - **Recommendation**: 60-600 seconds

### Scanner Configuration

- **`WIFISCAN_COLLECTOR_WIRELESS_INTERFACE`**: Network interface name
  - **Default**: Auto-detect
  - **Type**: String
  - **Examples**: `wlan0`, `wlp3s0`, `wlx001122334455`
  - **Auto-detection**: Prefers wlan0 > wlan1 > wlp* > wlx*

- **`WIFISCAN_COLLECTOR_SCAN_INTERVAL`**: Seconds between scans
  - **Default**: `5`
  - **Type**: Integer
  - **Range**: 1-3600
  - **Recommendation**: 5-60 seconds

- **`WIFISCAN_COLLECTOR_SCAN_TIMEOUT`**: Scan command timeout
  - **Default**: `30`
  - **Type**: Integer
  - **Range**: 5-300
  - **Note**: Adjust based on network density

### Retry and Logging Configuration

- **`WIFISCAN_COLLECTOR_MAX_RETRIES`**: Scan failures before interface check
  - **Default**: `3`
  - **Type**: Integer
  - **Range**: 1-20

- **`WIFISCAN_COLLECTOR_RETRY_DELAY`**: Delay after interface check failure
  - **Default**: `2`
  - **Type**: Integer
  - **Range**: 1-60

- **`WIFISCAN_COLLECTOR_LOG_LEVEL`**: Logging verbosity
  - **Default**: `INFO`
  - **Type**: String
  - **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`

- **`WIFISCAN_COLLECTOR_STATUS_LOG_INTERVAL`**: Status update frequency
  - **Default**: `300`
  - **Type**: Integer
  - **Range**: 30-3600
  - **Note**: 0 disables status logging

## Configuration Examples

### Basic Configuration

Minimal setup for testing:
```bash
# Required settings
WIFISCAN_COLLECTOR_INFLUXDB_TOKEN=your-token-here
WIFISCAN_COLLECTOR_INFLUXDB_ORG=your-org

# Optional - use defaults
WIFISCAN_COLLECTOR_INFLUXDB_URL=http://localhost:8086
WIFISCAN_COLLECTOR_INFLUXDB_BUCKET=wifiscan
```

### Production Configuration

Balanced settings for production:
```bash
# InfluxDB
WIFISCAN_COLLECTOR_INFLUXDB_URL=http://influxdb:8086
WIFISCAN_COLLECTOR_INFLUXDB_TOKEN=your-production-token
WIFISCAN_COLLECTOR_INFLUXDB_ORG=production-org
WIFISCAN_COLLECTOR_INFLUXDB_BUCKET=wifi-networks
WIFISCAN_COLLECTOR_INFLUXDB_TIMEOUT=60000

# Batch writing
WIFISCAN_COLLECTOR_BATCH_SIZE=200
WIFISCAN_COLLECTOR_BATCH_INTERVAL=30
WIFISCAN_COLLECTOR_BATCH_RETRY_INTERVAL=10
WIFISCAN_COLLECTOR_FLUSH_ON_SCAN=false

# Circuit breaker
WIFISCAN_COLLECTOR_MAX_BUFFER_SIZE=5000
WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_THRESHOLD=5
WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_TIMEOUT=300

# Scanner
WIFISCAN_COLLECTOR_WIRELESS_INTERFACE=wlan0
WIFISCAN_COLLECTOR_SCAN_INTERVAL=10
WIFISCAN_COLLECTOR_SCAN_TIMEOUT=45

# Logging
WIFISCAN_COLLECTOR_LOG_LEVEL=INFO
WIFISCAN_COLLECTOR_STATUS_LOG_INTERVAL=300
```

### High-Frequency Configuration

For dense network environments:
```bash
# Fast scanning
WIFISCAN_COLLECTOR_SCAN_INTERVAL=2
WIFISCAN_COLLECTOR_SCAN_TIMEOUT=60

# Frequent writes
WIFISCAN_COLLECTOR_BATCH_SIZE=50
WIFISCAN_COLLECTOR_BATCH_INTERVAL=5
WIFISCAN_COLLECTOR_FLUSH_ON_SCAN=true

# Larger buffer
WIFISCAN_COLLECTOR_MAX_BUFFER_SIZE=20000

# More verbose logging
WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG
WIFISCAN_COLLECTOR_STATUS_LOG_INTERVAL=60
```

### Low-Resource Configuration

For resource-constrained environments:
```bash
# Slower scanning
WIFISCAN_COLLECTOR_SCAN_INTERVAL=30
WIFISCAN_COLLECTOR_SCAN_TIMEOUT=20

# Larger batches
WIFISCAN_COLLECTOR_BATCH_SIZE=500
WIFISCAN_COLLECTOR_BATCH_INTERVAL=60

# Smaller buffer
WIFISCAN_COLLECTOR_MAX_BUFFER_SIZE=2000

# Less frequent status updates
WIFISCAN_COLLECTOR_STATUS_LOG_INTERVAL=900
```

### Critical Data Collection

Minimize data loss:
```bash
# Immediate writes
WIFISCAN_COLLECTOR_FLUSH_ON_SCAN=true
WIFISCAN_COLLECTOR_BATCH_SIZE=10
WIFISCAN_COLLECTOR_BATCH_INTERVAL=1

# Aggressive circuit breaker
WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_THRESHOLD=2
WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_TIMEOUT=30

# Small buffer
WIFISCAN_COLLECTOR_MAX_BUFFER_SIZE=500
```

## Configuration File Usage

### .env File

Create a `.env` file in the project root:
```bash
# Copy example and customize
cp .env.example .env
```

Edit `.env`:
```env
# InfluxDB Configuration
WIFISCAN_COLLECTOR_INFLUXDB_URL=http://influxdb:8086
WIFISCAN_COLLECTOR_INFLUXDB_TOKEN=your-token-here
WIFISCAN_COLLECTOR_INFLUXDB_ORG=your-org
WIFISCAN_COLLECTOR_INFLUXDB_BUCKET=wifiscan

# Scanner Configuration
WIFISCAN_COLLECTOR_WIRELESS_INTERFACE=wlan0
WIFISCAN_COLLECTOR_SCAN_INTERVAL=10
WIFISCAN_COLLECTOR_LOG_LEVEL=INFO
```

### Docker Compose

Use environment file with Docker Compose:
```yaml
services:
  wifiscan-collector:
    image: lux4rd0/wifiscan-collector:latest
    env_file:
      - .env
    cap_add:
      - NET_ADMIN
    network_mode: host
    restart: unless-stopped
```

### Kubernetes

Use ConfigMap and Secret:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wifiscan-config
data:
  WIFISCAN_COLLECTOR_INFLUXDB_URL: "http://influxdb:8086"
  WIFISCAN_COLLECTOR_INFLUXDB_ORG: "your-org"
  WIFISCAN_COLLECTOR_INFLUXDB_BUCKET: "wifiscan"
  WIFISCAN_COLLECTOR_SCAN_INTERVAL: "10"
  WIFISCAN_COLLECTOR_LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: wifiscan-secret
type: Opaque
stringData:
  WIFISCAN_COLLECTOR_INFLUXDB_TOKEN: "your-token-here"
```

## Performance Tuning

### Memory Usage

Buffer size affects memory usage:
- Each point: ~500 bytes
- 10,000 points: ~5MB
- Monitor with status logs

### CPU Usage

Scanning frequency affects CPU:
- Parsing is CPU-intensive
- Longer intervals reduce CPU load
- Consider scan timeout for dense networks

### Network Usage

Batch settings affect network traffic:
- Larger batches = fewer requests
- Smaller batches = lower latency
- Balance based on network capacity

### InfluxDB Performance

Optimize for InfluxDB:
- Batch size: 100-1000 points
- Timeout: 30-60 seconds
- Use appropriate retention policies

## Security Configuration

### Token Management

- Use least-privilege tokens
- Rotate tokens regularly
- Store securely (environment variables, secrets)
- Never commit to version control

### Network Security

- Use HTTPS for InfluxDB connections
- Implement network segmentation
- Use firewall rules
- Monitor access logs

### Container Security

- Run with minimal privileges
- Use non-root user when possible
- Limit capabilities (only NET_ADMIN needed)
- Use security-focused base images

## Validation and Testing

### Configuration Validation

The application validates all configuration on startup:
- Type checking
- Range validation
- Required field checking
- Format validation

### Testing Configuration

Test with different settings:
```bash
# Test with debug logging
WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG python src/wifiscan-collector.py

# Test with immediate flush
WIFISCAN_COLLECTOR_FLUSH_ON_SCAN=true python src/wifiscan-collector.py

# Test circuit breaker
WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_THRESHOLD=1 python src/wifiscan-collector.py
```

## Migration Guide

### From Previous Versions

If upgrading from an older version:

1. Update environment variable names (add `WIFISCAN_COLLECTOR_` prefix)
2. Review new configuration options
3. Test with existing data
4. Update Docker Compose files
5. Check for breaking changes in CHANGELOG.md

### Configuration Changes

Notable changes in 2025.7.0:
- Added circuit breaker configuration
- Added buffer size limits
- Added status logging intervals
- Changed from hardcoded to configurable interface
- Added production readiness options

## Troubleshooting Configuration

### Common Issues

1. **Invalid token**: Check token format and permissions
2. **Connection refused**: Verify InfluxDB URL and network connectivity
3. **Interface not found**: Check interface name and permissions
4. **High memory usage**: Reduce buffer size or increase flush frequency

### Debug Configuration

Enable debug logging to troubleshoot:
```bash
WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG
```

Check configuration loading:
```bash
# Application logs configuration on startup
docker logs wifiscan-collector | grep "Configuration loaded"
```

### Validation Errors

Configuration validation errors show:
- Field name
- Invalid value
- Expected type/range
- Validation rule

Fix validation errors by:
1. Checking environment variable names
2. Verifying value types
3. Ensuring values are in valid ranges
4. Providing required fields

## Best Practices

### General Guidelines

1. Use `.env` files for local development
2. Use secrets management for production
3. Test configuration changes in staging
4. Monitor application logs for issues
5. Document custom configurations

### Performance Optimization

1. Tune batch size based on network density
2. Adjust scan intervals for CPU usage
3. Monitor buffer usage during outages
4. Use appropriate circuit breaker settings
5. Balance write frequency vs. data loss tolerance

### Security Best Practices

1. Use read-only tokens when possible
2. Implement token rotation
3. Use secure communication (HTTPS)
4. Monitor access patterns
5. Implement proper logging