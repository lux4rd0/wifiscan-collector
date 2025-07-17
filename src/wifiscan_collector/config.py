"""Configuration module for WiFi Scanner.

This module provides configuration management using Pydantic settings.
All configuration is loaded from environment variables with the
WIFISCAN_COLLECTOR_ prefix.

Example:
    Basic configuration:
        WIFISCAN_COLLECTOR_INFLUXDB_TOKEN=your-token
        WIFISCAN_COLLECTOR_INFLUXDB_ORG=your-org

    Create config instance:
        config = Config()
"""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration.

    All configuration is loaded from environment variables with the
    WIFISCAN_COLLECTOR_ prefix. Supports .env files for local development.

    Attributes:
        influxdb_url: URL of the InfluxDB instance
        influxdb_token: Authentication token for InfluxDB
        influxdb_org: InfluxDB organization name
        influxdb_bucket: InfluxDB bucket name for storing data
        influxdb_timeout: Connection timeout in milliseconds
        batch_size: Number of points to batch before writing
        batch_interval: Maximum seconds to wait before flushing batch
        batch_retry_interval: Retry interval for failed batches
        flush_on_scan: Whether to flush batch after each scan
        max_buffer_size: Maximum points to buffer in memory
        circuit_breaker_threshold: Failures before opening circuit
        circuit_breaker_timeout: Seconds before testing circuit again
        wireless_interface: Network interface name (None for auto-detect)
        scan_interval: Seconds between WiFi scans
        scan_timeout: Timeout for scan command
        max_retries: Max consecutive scan failures before interface check
        retry_delay: Delay after interface check failure
        log_level: Logging verbosity level
        status_log_interval: Frequency of status updates in seconds
    """

    model_config = SettingsConfigDict(
        env_prefix="WIFISCAN_COLLECTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # InfluxDB settings
    influxdb_url: str = Field(
        default="http://localhost:8086", description="InfluxDB URL"
    )
    influxdb_token: str = Field(description="InfluxDB authentication token")
    influxdb_org: str = Field(description="InfluxDB organization")
    influxdb_bucket: str = Field(default="wifiscan", description="InfluxDB bucket name")
    influxdb_timeout: int = Field(
        default=30000, description="InfluxDB timeout in milliseconds"
    )

    # Batch settings
    batch_size: int = Field(
        default=100, description="Number of points to batch before writing to InfluxDB"
    )
    batch_interval: int = Field(
        default=10, description="Maximum seconds to wait before flushing batch"
    )
    batch_retry_interval: int = Field(
        default=5, description="Retry interval in seconds for failed batches"
    )
    max_buffer_size: int = Field(
        default=10000, description="Maximum number of points to buffer in memory"
    )
    max_retry_attempts: int = Field(
        default=10, description="Maximum retry attempts before entering backoff mode"
    )
    circuit_breaker_threshold: int = Field(
        default=5, description="Consecutive failures before opening circuit"
    )
    circuit_breaker_timeout: int = Field(
        default=300, description="Seconds to wait before testing circuit again"
    )
    flush_on_scan: bool = Field(
        default=False,
        description="Flush batch after each scan (reduces data loss risk)",
    )

    # Scanner settings
    wireless_interface: str | None = Field(
        default=None,
        description="Wireless interface to scan (auto-detect if not specified)",
    )
    scan_interval: int = Field(
        default=5, description="Interval between scans in seconds"
    )
    scan_timeout: int = Field(default=30, description="Scan command timeout in seconds")

    # Retry settings
    max_retries: int = Field(
        default=3,
        description="Maximum consecutive scan failures before interface check",
    )
    retry_delay: int = Field(
        default=2, description="Delay after interface check failure in seconds"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    status_log_interval: int = Field(
        default=300, description="Log summary status every N seconds (0 to disable)"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level.

        Args:
            v: The log level string to validate

        Returns:
            The validated log level in uppercase

        Raises:
            ValueError: If log level is not valid
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("scan_interval", "scan_timeout", "batch_size", "batch_interval")
    @classmethod
    def validate_positive(cls, v: int, info: Any) -> int:
        """Validate that integer fields are positive.

        Args:
            v: The integer value to validate
            info: Field information from Pydantic

        Returns:
            The validated integer value

        Raises:
            ValueError: If value is less than 1
        """
        if v < 1:
            raise ValueError(f"{info.field_name} must be at least 1")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Validate max retries is non-negative.

        Args:
            v: The max retries value to validate

        Returns:
            The validated max retries value

        Raises:
            ValueError: If value is negative
        """
        if v < 0:
            raise ValueError("max_retries must be non-negative")
        return v
