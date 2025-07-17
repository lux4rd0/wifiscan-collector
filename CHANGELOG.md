# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2025.7.0] - 2025-07-17

### 🚀 Major Features

**Modern Async Architecture**
- Complete rewrite using Python 3.13+ async/await for improved performance
- Fully asynchronous scanning, storage, and configuration management
- Concurrent operations with proper resource management

**Advanced WiFi Detection**
- WiFi 6/6E (802.11ax) support with HE capability detection
- WPA3 and OWE security protocol detection
- Channel width analysis (20/40/80/160 MHz and 80+80 MHz)
- Maximum transmit power tracking
- Enhanced band classification (2.4GHz, 5GHz, 6GHz)

**Intelligent Interface Management**
- Automatic wireless interface discovery and selection
- Smart preference ordering: wlan0 > wlan1 > wlp* > wlx*
- Administrative vs operational state detection
- Detailed interface information logging (MAC, type, connection status)

**Production-Ready Storage**
- Circuit breaker pattern for InfluxDB reliability
- Memory-efficient FIFO buffering with overflow protection
- Configurable batch processing with automatic flush
- Exponential backoff retry mechanism
- Graceful degradation during outages

### 🛠️ Infrastructure & Reliability

**Monitoring & Observability**
- Comprehensive health monitoring with buffer and circuit breaker status
- Performance metrics: scan rates, success rates, storage statistics
- Human-readable uptime tracking (e.g., "2d 3h", "1h 30m")
- Periodic status logging with configurable intervals

**Configuration & Deployment**
- Pydantic-based configuration with comprehensive validation
- Environment variable support with `WIFISCAN_COLLECTOR_` prefix
- Secure handling of sensitive values with automatic obfuscation
- Docker containerization with multi-stage builds
- Support for .env files in development

**Error Handling & Recovery**
- Graceful shutdown with proper signal handling (SIGTERM/SIGINT)
- Resource cleanup and data preservation on shutdown
- Comprehensive error recovery mechanisms
- Detailed logging with configurable levels

### 📊 Data Collection Enhancements

**Network Information**
- Enhanced parsing of modern WiFi standards (802.11n/ac/ax)
- Improved signal strength extraction with dBm accuracy
- Security protocol detection including encryption types
- Access point capability analysis
- Hidden network handling

**Storage Optimization**
- Batch writing with configurable sizes and intervals
- Connection pooling for InfluxDB operations
- Memory usage optimization during outages
- Data integrity protection with buffer management

### 🔧 Developer Experience

**Code Quality**
- Google-style docstrings throughout the codebase
- Complete type hints for Python 3.13
- Modular architecture with clean separation of concerns
- Comprehensive test coverage (21 tests)
- Passes all quality checks: Black, Ruff, Flake8, MyPy

**Documentation**
- User-focused README with quick start guide
- Detailed developer documentation in docs/ directory
- Configuration reference with examples
- Troubleshooting guide for common deployment issues

### 🐛 Critical Fixes

**Interface Detection**
- Fixed misleading log messages about interface UP/DOWN states
- Corrected logic to require administrative UP (not operational UP) for scanning
- Improved interface state detection and reporting

**Memory & Performance**
- Resolved memory leaks from unclosed InfluxDB connections
- Fixed unbounded memory growth during InfluxDB outages
- Eliminated race conditions in concurrent operations
- Improved subprocess handling with proper cleanup

**Platform Compatibility**
- Fixed ARM platform builds with conditional gcc installation
- Added missing `ip` command support in Docker containers
- Resolved dependency issues with influxdb-client async extensions

### 🔒 Security Improvements

- Token and password obfuscation in logs
- Secure configuration validation
- Input sanitization for all user-provided values
- Removal of potential command injection vulnerabilities

### 📦 Project Structure

```
src/
├── wifiscan-collector.py      # Entry point script
└── wifiscan_collector/
    ├── __init__.py            # Package initialization
    ├── config.py              # Configuration management
    ├── main.py                # Application orchestration
    ├── models.py              # Data models
    ├── scanner.py             # WiFi scanning logic
    ├── storage.py             # InfluxDB storage
    ├── utils.py               # Utility functions
    └── version.py             # Version handling

docs/
├── configuration.md           # Configuration reference
├── development.md             # Development guide
└── troubleshooting.md         # Problem solving

tests/
├── conftest.py                # Test configuration
├── test_config.py             # Configuration tests
├── test_models.py             # Model tests
├── test_scanner.py            # Scanner tests
└── test_utils.py              # Utility tests
```

### 🚮 Removed

- Legacy synchronous scanning implementation
- Hardcoded configuration values and global variables
- Print statements (replaced with structured logging)
- Deprecated Python patterns and manual string formatting
- Unused dependencies and deprecated configuration options

---

## Migration Guide

This release represents a complete modernization from earlier versions:

- **Configuration**: All settings now use `WIFISCAN_COLLECTOR_` environment variables
- **Dependencies**: Requires Python 3.13+ and updated package versions
- **Deployment**: New Docker image with improved security and performance
- **Monitoring**: Enhanced logging and health monitoring capabilities

For detailed migration instructions, see the [development documentation](docs/development.md).

## Contributors

This release includes contributions to architecture, reliability, documentation, and code quality improvements that make this project production-ready for open source deployment.