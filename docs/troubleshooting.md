# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the WiFiScan Collector.

## Quick Diagnostics

### Check Application Status

```bash
# View recent logs
docker logs --tail 50 wifiscan-collector

# Follow logs in real-time
docker logs -f wifiscan-collector

# Check container status
docker ps | grep wifiscan-collector
```

### Check System Resources

```bash
# Memory usage
docker stats wifiscan-collector --no-stream

# CPU usage
top -p $(docker inspect --format '{{.State.Pid}}' wifiscan-collector)
```

## Common Issues

### 1. Permission Denied Errors

**Symptoms:**
- "Operation not permitted" errors
- "Permission denied" when accessing wireless interface
- Interface scanning fails

**Solutions:**

1. **Ensure NET_ADMIN capability:**
   ```bash
   # Docker run
   docker run --cap-add=NET_ADMIN ...
   
   # Docker Compose
   services:
     wifiscan-collector:
       cap_add:
         - NET_ADMIN
   ```

2. **Check container privileges:**
   ```bash
   docker exec wifiscan-collector capsh --print
   ```

3. **Verify interface permissions:**
   ```bash
   # Check if interface is accessible
   docker exec wifiscan-collector ip link show
   docker exec wifiscan-collector iw list
   ```

### 2. Interface Not Found

**Symptoms:**
- "Interface wlan0 not found" errors
- "No wireless interfaces found" messages
- Auto-detection fails

**Diagnosis:**

1. **Check available interfaces:**
   ```bash
   # On host system
   ip link show
   iwconfig
   
   # In container
   docker exec wifiscan-collector ip link show
   ```

2. **Verify wireless capability:**
   ```bash
   # Check for wireless interfaces
   ls /sys/class/net/*/wireless
   
   # Check interface details
   iw list
   ```

**Solutions:**

1. **Specify correct interface:**
   ```bash
   export WIFISCAN_COLLECTOR_WIRELESS_INTERFACE=wlp3s0
   ```

2. **Use host networking:**
   ```yaml
   services:
     wifiscan-collector:
       network_mode: host
   ```

3. **Check interface naming:**
   ```bash
   # Modern naming (Predictable Network Interface Names)
   # PCI: wlp3s0 (PCI bus 3, slot 0)
   # USB: wlx001122334455 (USB with MAC address)
   # Traditional: wlan0, wlan1
   ```

### 3. Interface Not Administratively UP

**Symptoms:**
- "Interface wlan0 is not UP" warnings
- Scanning fails or returns no results
- Interface exists but cannot scan

**Diagnosis:**

```bash
# Check interface status
ip link show wlan0

# Look for flags - should include UP
# Good: <BROADCAST,MULTICAST,UP>
# Bad:  <BROADCAST,MULTICAST> (missing UP)
```

**Solutions:**

1. **Bring interface up:**
   ```bash
   sudo ip link set wlan0 up
   ```

2. **Persistent interface configuration:**
   ```bash
   # Add to /etc/rc.local or systemd service
   ip link set wlan0 up
   ```

3. **Check for interface blocking:**
   ```bash
   # Check if interface is blocked
   rfkill list all
   
   # Unblock if needed
   sudo rfkill unblock wifi
   ```

**Important Notes:**
- Interface can show `state DOWN` or `NO-CARRIER` - this is normal
- Only administrative UP state is required for scanning
- Interface doesn't need to be connected to any network

### 4. No Scan Results

**Symptoms:**
- Scanning completes but finds no networks
- "No networks found in scan" warnings
- Empty scan results

**Diagnosis:**

1. **Manual scan test:**
   ```bash
   # Test scanning manually
   sudo iw dev wlan0 scan | head -20
   
   # Check for nearby networks
   sudo iw dev wlan0 scan | grep -E "(BSS|SSID|signal)"
   ```

2. **Check interface capabilities:**
   ```bash
   # Verify scanning capability
   iw phy phy0 info | grep -A 10 "Supported commands"
   ```

**Solutions:**

1. **Verify interface supports scanning:**
   ```bash
   # Should show "scan" in supported commands
   iw phy phy0 info | grep -A 20 "Supported commands"
   ```

2. **Check for hardware issues:**
   ```bash
   # Check dmesg for hardware errors
   dmesg | grep -i wifi
   dmesg | grep -i wireless
   ```

3. **Adjust scan timeout:**
   ```bash
   export WIFISCAN_COLLECTOR_SCAN_TIMEOUT=60
   ```

4. **Check environment factors:**
   - No WiFi networks in range
   - Faraday cage or RF shielding
   - Interference from other devices

### 5. InfluxDB Connection Errors

**Symptoms:**
- "Failed to connect to InfluxDB" errors
- "Connection refused" messages
- "Authentication failed" errors

**Diagnosis:**

1. **Test InfluxDB connectivity:**
   ```bash
   # Basic connectivity
   curl -i http://influxdb:8086/ping
   
   # Test with authentication
   curl -H "Authorization: Token your-token" \
        http://influxdb:8086/api/v2/buckets
   ```

2. **Check container networking:**
   ```bash
   # Test from container
   docker exec wifiscan-collector curl -i http://influxdb:8086/ping
   
   # Check DNS resolution
   docker exec wifiscan-collector nslookup influxdb
   ```

**Solutions:**

1. **Verify InfluxDB is running:**
   ```bash
   docker ps | grep influxdb
   docker logs influxdb
   ```

2. **Check network connectivity:**
   ```bash
   # Same Docker network
   docker network ls
   docker network inspect bridge
   ```

3. **Verify credentials:**
   ```bash
   # Test token with InfluxDB CLI
   influx auth list --token your-token
   ```

4. **Check firewall/network policies:**
   ```bash
   # Port accessibility
   netstat -tlnp | grep 8086
   ```

### 6. High Memory Usage

**Symptoms:**
- Container using excessive memory
- Out of memory errors
- Performance degradation

**Diagnosis:**

1. **Check memory usage:**
   ```bash
   # Container memory
   docker stats wifiscan-collector --no-stream
   
   # Process memory
   docker exec wifiscan-collector ps aux
   ```

2. **Check buffer status:**
   ```bash
   # Look for buffer size in logs
   docker logs wifiscan-collector | grep -i buffer
   ```

**Solutions:**

1. **Reduce buffer size:**
   ```bash
   export WIFISCAN_COLLECTOR_MAX_BUFFER_SIZE=5000
   ```

2. **Increase flush frequency:**
   ```bash
   export WIFISCAN_COLLECTOR_BATCH_INTERVAL=5
   export WIFISCAN_COLLECTOR_FLUSH_ON_SCAN=true
   ```

3. **Monitor buffer usage:**
   ```bash
   # Enable status logging
   export WIFISCAN_COLLECTOR_STATUS_LOG_INTERVAL=60
   ```

### 7. Circuit Breaker Issues

**Symptoms:**
- "Circuit breaker OPEN" messages
- Data not being written to InfluxDB
- Continuous retry messages

**Diagnosis:**

1. **Check circuit breaker status:**
   ```bash
   # Look for circuit breaker logs
   docker logs wifiscan-collector | grep -i circuit
   ```

2. **Check InfluxDB health:**
   ```bash
   curl -i http://influxdb:8086/health
   ```

**Solutions:**

1. **Adjust circuit breaker settings:**
   ```bash
   # More tolerant settings
   export WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_THRESHOLD=10
   export WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_TIMEOUT=60
   ```

2. **Fix underlying InfluxDB issues:**
   - Check InfluxDB logs
   - Verify disk space
   - Check database performance

3. **Force circuit reset:**
   ```bash
   # Restart container to reset circuit breaker
   docker restart wifiscan-collector
   ```

### 8. Scanning Performance Issues

**Symptoms:**
- Slow scan completion
- High CPU usage
- Scan timeouts

**Diagnosis:**

1. **Check scan timing:**
   ```bash
   # Enable debug logging
   export WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG
   
   # Look for scan duration
   docker logs wifiscan-collector | grep -i "scan.*completed"
   ```

2. **Test manual scan performance:**
   ```bash
   time sudo iw dev wlan0 scan > /dev/null
   ```

**Solutions:**

1. **Adjust scan timeout:**
   ```bash
   export WIFISCAN_COLLECTOR_SCAN_TIMEOUT=60
   ```

2. **Increase scan interval:**
   ```bash
   export WIFISCAN_COLLECTOR_SCAN_INTERVAL=30
   ```

3. **Check for interference:**
   - Multiple scanning tools running
   - Network congestion
   - Hardware limitations

## Debug Mode

### Enable Debug Logging

```bash
export WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG
```

### Debug Information

Debug mode provides:
- Detailed scan timings
- Network parsing details
- InfluxDB write details
- Circuit breaker state changes
- Buffer usage statistics

### Log Analysis

```bash
# Filter by component
docker logs wifiscan-collector | grep "scanner"
docker logs wifiscan-collector | grep "storage"
docker logs wifiscan-collector | grep "circuit"

# Check for errors
docker logs wifiscan-collector | grep -i error

# Monitor performance
docker logs wifiscan-collector | grep -E "(scan.*completed|wrote.*points)"
```

## System Information

### Collect System Information

```bash
# Container information
docker inspect wifiscan-collector

# System information
uname -a
lscpu
free -h
df -h

# Network interfaces
ip link show
iwconfig
iw list

# InfluxDB information
curl -i http://influxdb:8086/ping
```

### Environment Variables

```bash
# Check current configuration
docker exec wifiscan-collector env | grep WIFISCAN_COLLECTOR
```

## Performance Monitoring

### Key Metrics to Monitor

1. **Scan Performance:**
   - Scan completion time
   - Networks found per scan
   - Scan failure rate

2. **Memory Usage:**
   - Container memory consumption
   - Buffer size and usage
   - Point drop rate

3. **Network Performance:**
   - InfluxDB write success rate
   - Circuit breaker state
   - Write latency

### Status Logging

Enable periodic status updates:
```bash
export WIFISCAN_COLLECTOR_STATUS_LOG_INTERVAL=300
```

Status logs include:
- Scan statistics
- Storage statistics
- Buffer usage
- Error rates

## Common Error Messages

### "Operation not permitted"
- **Cause**: Missing NET_ADMIN capability
- **Solution**: Add `--cap-add=NET_ADMIN` to Docker run command

### "Interface wlan0 not found"
- **Cause**: Interface name incorrect or missing
- **Solution**: Check available interfaces with `ip link show`

### "Circuit breaker OPEN"
- **Cause**: Too many consecutive InfluxDB write failures
- **Solution**: Check InfluxDB health and adjust circuit breaker settings

### "Buffer near capacity"
- **Cause**: InfluxDB unavailable, buffer filling up
- **Solution**: Fix InfluxDB connectivity or increase buffer size

### "Scan timed out"
- **Cause**: Scan taking longer than timeout setting
- **Solution**: Increase `WIFISCAN_COLLECTOR_SCAN_TIMEOUT`

## Getting Help

### Information to Provide

When reporting issues, include:

1. **System Information:**
   - OS version
   - Docker version
   - Container image tag

2. **Configuration:**
   - Environment variables (without sensitive data)
   - Docker Compose configuration

3. **Logs:**
   - Complete error messages
   - Relevant log entries
   - Debug output if available

4. **Environment:**
   - Network setup
   - InfluxDB version
   - Wireless hardware

### Log Collection

```bash
# Collect comprehensive logs
docker logs wifiscan-collector --since 1h > wifiscan-logs.txt

# Include system information
docker inspect wifiscan-collector > container-info.json
docker exec wifiscan-collector ip link show > interface-info.txt
```

### Test Cases

Before reporting issues, test:

1. **Manual scanning:**
   ```bash
   sudo iw dev wlan0 scan | head -20
   ```

2. **InfluxDB connectivity:**
   ```bash
   curl -i http://influxdb:8086/ping
   ```

3. **Container networking:**
   ```bash
   docker exec wifiscan-collector ping influxdb
   ```

4. **Interface status:**
   ```bash
   ip link show wlan0
   ```

These test results help identify the root cause of issues.

## Performance Optimization

### For High-Density Networks

```bash
# Increase timeouts
export WIFISCAN_COLLECTOR_SCAN_TIMEOUT=90

# Larger batches
export WIFISCAN_COLLECTOR_BATCH_SIZE=500

# Less frequent scanning
export WIFISCAN_COLLECTOR_SCAN_INTERVAL=30
```

### For Low-Resource Systems

```bash
# Smaller buffers
export WIFISCAN_COLLECTOR_MAX_BUFFER_SIZE=2000

# Longer intervals
export WIFISCAN_COLLECTOR_SCAN_INTERVAL=60
export WIFISCAN_COLLECTOR_BATCH_INTERVAL=30
```

### For Critical Applications

```bash
# Immediate flushing
export WIFISCAN_COLLECTOR_FLUSH_ON_SCAN=true

# Aggressive circuit breaker
export WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_THRESHOLD=3
export WIFISCAN_COLLECTOR_CIRCUIT_BREAKER_TIMEOUT=30
```