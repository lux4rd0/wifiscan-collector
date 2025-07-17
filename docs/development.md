# Development Guide

This guide covers development setup, testing, code quality, and contribution guidelines for the WiFiScan Collector.

## Development Setup

### Prerequisites

- Python 3.13+
- Git
- Linux system with wireless capabilities
- `iw` tool installed

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/lux4rd0/wifiscan-collector.git
   cd wifiscan-collector
   ```

2. **Create virtual environment:**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Code Quality

The project enforces strict code quality standards using multiple tools:

### Formatting
- **Black**: Code formatter with 88-character line limit
- **isort**: Import sorting (integrated with Black)

### Linting
- **Ruff**: Fast Python linter (replaces flake8, pylint, isort)
- **Flake8**: Additional style checking
- **MyPy**: Static type checking

### Running Quality Checks

Run all quality checks:
```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Check style
flake8 src/ tests/

# Check types
mypy src/ --ignore-missing-imports
```

Or run everything at once:
```bash
black src/ tests/ && ruff check src/ tests/ && flake8 src/ tests/ && mypy src/ --ignore-missing-imports
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run quality checks:
```bash
pip install pre-commit
pre-commit install
```

## Testing

### Test Structure

```
tests/
├── conftest.py           # Pytest configuration and fixtures
├── test_config.py        # Configuration tests
├── test_models.py        # Data model tests
├── test_scanner.py       # WiFi scanner tests
├── test_storage.py       # InfluxDB storage tests
└── test_utils.py         # Utility function tests
```

### Running Tests

Run all tests:
```bash
pytest -v
```

Run with coverage:
```bash
pytest -v --cov=src --cov-report=term-missing
```

Run specific test file:
```bash
pytest tests/test_scanner.py -v
```

Run specific test:
```bash
pytest tests/test_scanner.py::TestWifiScanner::test_parse_iw_output -v
```

### Test Coverage

The project maintains high test coverage across all modules:
- Configuration validation
- WiFi network parsing
- InfluxDB storage operations
- Circuit breaker functionality
- Interface discovery
- Utility functions

### Writing Tests

- Use pytest fixtures for common setup
- Test both success and failure scenarios
- Mock external dependencies (InfluxDB, subprocess calls)
- Include edge cases and error conditions
- Follow naming convention: `test_function_name_scenario`

## Project Structure

```
src/
├── wifiscan-collector.py      # Entry point wrapper
└── wifiscan_collector/
    ├── __init__.py            # Package initialization
    ├── config.py              # Pydantic configuration models
    ├── main.py                # Application entry point
    ├── models.py              # Data models (WifiNetwork)
    ├── scanner.py             # WiFi scanning logic
    ├── storage.py             # InfluxDB storage handler
    ├── utils.py               # Utility functions
    └── version.py             # Version detection

tests/
├── conftest.py                # Pytest configuration
├── test_config.py             # Configuration tests
├── test_models.py             # Model tests
├── test_scanner.py            # Scanner tests
├── test_storage.py            # Storage tests
└── test_utils.py              # Utility tests

docs/
├── development.md             # This file
├── configuration.md           # Detailed configuration guide
└── troubleshooting.md         # Extended troubleshooting guide
```

## Code Style Guidelines

### Python Style
- Follow PEP 8 with 88-character line limit
- Use type hints for all functions and methods
- Use docstrings for all public functions
- Prefer `pathlib` over `os.path`
- Use f-strings for string formatting

### Async/Await
- Use `async`/`await` for I/O operations
- Use `asyncio.create_subprocess_exec` for subprocess calls
- Properly handle `asyncio.CancelledError`
- Use context managers for resource cleanup

### Error Handling
- Use specific exception types
- Log errors with appropriate levels
- Sanitize sensitive data in error messages
- Include context in error messages

### Testing
- Test async functions with `@pytest.mark.asyncio`
- Use `unittest.mock` for mocking
- Test both success and failure paths
- Use descriptive test names

## Configuration

The project uses Pydantic for configuration management:

### Adding New Configuration Options

1. Add field to `Config` class in `config.py`
2. Include default value and description
3. Add validation if needed
4. Update `.env.example`
5. Add tests in `test_config.py`
6. Update documentation

### Environment Variables

All configuration uses the `WIFISCAN_COLLECTOR_` prefix:
- Use uppercase for environment variables
- Use lowercase for Python field names
- Include type hints and descriptions
- Provide sensible defaults

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run all quality checks (formatting, linting, type checking)
5. Run the test suite and ensure all tests pass
6. Update documentation if needed
7. Commit your changes: `git commit -m 'Add amazing feature'`
8. Push to the branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests liberally

### Code Review

- All changes require code review
- Address all review comments
- Ensure CI passes before merging
- Squash commits when merging

## Release Process

1. Update version in directory structure (2025/7/x)
2. Update CHANGELOG.md
3. Run full test suite
4. Create release tag
5. Build and push Docker image
6. Update documentation

## Debugging

### Development Environment

Enable debug logging:
```bash
export WIFISCAN_COLLECTOR_LOG_LEVEL=DEBUG
```

### Common Development Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Test failures**: Check for proper mocking of external dependencies
3. **Type errors**: Run `mypy src/` to check type annotations
4. **Format errors**: Run `black src/ tests/` to fix formatting

### Debugging Network Issues

Test interface manually:
```bash
# Check interface status
ip link show wlan0

# Test scanning
sudo iw dev wlan0 scan | head -20
```

### Debugging InfluxDB Issues

Use InfluxDB CLI to verify data:
```bash
influx query 'from(bucket:"wifiscan") |> range(start: -1h) |> limit(n:10)'
```

## Performance Considerations

### Memory Usage
- Monitor buffer size during development
- Test with various buffer limits
- Profile memory usage during long runs

### CPU Usage
- Scan interval affects CPU usage
- Parsing is CPU-intensive for large scan results
- Consider batch processing for performance

### Network Usage
- Batch size affects network traffic
- Circuit breaker prevents network flooding
- Monitor InfluxDB write performance

## Security Guidelines

### Sensitive Data
- Never commit secrets to version control
- Use environment variables for configuration
- Sanitize tokens in error messages
- Use secure defaults

### Dependencies
- Regularly update dependencies
- Review security advisories
- Use dependency scanning tools
- Pin versions in requirements.txt

## Documentation

### Code Documentation
- Use docstrings for all public functions
- Include parameter and return types
- Document exceptions that can be raised
- Include usage examples

### User Documentation
- Keep README.md user-focused
- Provide comprehensive configuration examples
- Include troubleshooting guides
- Update documentation with new features

## Support

- Check existing issues before creating new ones
- Include full error messages and logs
- Provide system information (OS, Python version)
- Include configuration (without sensitive data)