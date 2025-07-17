"""InfluxDB storage module with async batch writing.

This module provides robust, production-ready InfluxDB storage with advanced
reliability features including circuit breaker pattern, buffering, and
comprehensive error handling.

Key features:
- Async batch writing for optimal performance
- Circuit breaker pattern to prevent service hammering
- Configurable buffer with overflow protection
- Exponential backoff retry logic
- Health monitoring and statistics
- Graceful shutdown with data preservation
- Memory-efficient point buffering using deque

The storage system is designed for long-running processes and handles
InfluxDB outages gracefully while maintaining data integrity.

Example:
    Basic usage:
        config = Config()
        storage = InfluxDBStorage(config)

        await storage.start()
        await storage.add_networks(networks)
        await storage.stop()

    Health monitoring:
        health = await storage.health_check()
        print(f"Status: {health['status']}")
        print(f"Buffer: {health['buffer_size']}/{health['buffer_capacity']}")
"""

import asyncio
import contextlib
import logging
import time
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api_async import WriteApiAsync

from .config import Config
from .models import WifiNetwork

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states for InfluxDB connection management.

    The circuit breaker prevents continuous retry attempts when InfluxDB
    is unavailable, reducing resource usage and allowing faster recovery.

    States:
        CLOSED: Normal operation, requests allowed
        OPEN: Failures exceeded threshold, requests blocked
        HALF_OPEN: Testing if service recovered, limited requests allowed
    """

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceeded threshold
    HALF_OPEN = "half_open"  # Testing if service recovered


class InfluxDBStorage:
    """Production-ready InfluxDB storage with circuit breaker and buffering.

    This class provides comprehensive InfluxDB storage capabilities designed
    for long-running processes. It includes advanced reliability features
    to handle network outages, service interruptions, and resource constraints.

    Key features:
    - Async batch writing for optimal performance
    - Circuit breaker pattern prevents service hammering
    - Configurable buffer with overflow protection
    - Exponential backoff retry logic
    - Health monitoring and statistics
    - Graceful shutdown with data preservation
    - Memory-efficient FIFO buffering

    The storage system automatically handles:
    - InfluxDB connectivity issues
    - Network timeouts and failures
    - Memory pressure during outages
    - Data loss prevention
    - Performance optimization

    Example:
        config = Config()
        storage = InfluxDBStorage(config)

        # Start storage system
        await storage.start()

        # Add networks (automatically batched)
        await storage.add_networks(networks)

        # Check health
        health = await storage.health_check()

        # Graceful shutdown
        await storage.stop()
    """

    def __init__(self, config: Config):
        """Initialize storage with configuration.

        Args:
            config: Application configuration containing InfluxDB settings,
                   batch configuration, and circuit breaker parameters
        """
        self.config = config
        self._client: InfluxDBClientAsync | None = None
        self._write_api: WriteApiAsync | None = None

        # Use deque for efficient FIFO buffer with max size
        self._batch: deque[Point] = deque(maxlen=config.max_buffer_size)
        self._batch_lock = asyncio.Lock()

        # Circuit breaker state
        self._circuit_state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._circuit_opened_at: float | None = None

        # Statistics
        self._total_received = 0
        self._total_written = 0
        self._total_dropped = 0
        self._last_successful_write: datetime | None = None
        self._last_failure: datetime | None = None

        # Control
        self._running = True
        self._flush_task: asyncio.Task | None = None
        self._last_flush = asyncio.get_event_loop().time()

    async def start(self) -> None:
        """Start the storage system."""
        # Initialize InfluxDB client
        self._client = InfluxDBClientAsync(
            url=self.config.influxdb_url,
            token=self.config.influxdb_token,
            org=self.config.influxdb_org,
            timeout=self.config.influxdb_timeout,
        )

        self._write_api = self._client.write_api()

        # Test connection
        try:
            logger.info(
                f"Connected to InfluxDB at "
                f"{self._sanitize_url(self.config.influxdb_url)}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {self._sanitize_error(e)}")
            raise

        # Start background flush task
        self._flush_task = asyncio.create_task(self._periodic_flush())

    async def stop(self) -> None:
        """Stop the storage system and flush remaining data."""
        self._running = False

        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._flush_task

        # Flush any remaining data
        await self._flush_batch(force=True)

        # Close client
        if self._client:
            await self._client.close()

    async def add_networks(self, networks: list[WifiNetwork]) -> None:
        """Add networks to the batch with overflow protection."""
        points = [network.to_influxdb_point() for network in networks]

        async with self._batch_lock:
            self._total_received += len(points)

            # Check if we're about to overflow
            space_available = self.config.max_buffer_size - len(self._batch)
            if space_available < len(points):
                dropped = len(points) - space_available
                self._total_dropped += dropped
                logger.warning(
                    f"Buffer near capacity "
                    f"({len(self._batch)}/{self.config.max_buffer_size}), "
                    f"dropping {dropped} oldest points"
                )

            # Add points (deque will automatically drop oldest if maxlen exceeded)
            self._batch.extend(points)
            batch_size = len(self._batch)

        logger.debug(f"Added {len(points)} points to batch (total: {batch_size})")

        # Check if we should flush
        should_flush = batch_size >= self.config.batch_size or (
            self.config.flush_on_scan and len(points) > 0
        )

        if should_flush and self._circuit_state != CircuitState.OPEN:
            await self._flush_batch()

    async def _periodic_flush(self) -> None:
        """Periodically flush the batch based on time interval."""
        while self._running:
            try:
                await asyncio.sleep(self.config.batch_interval)

                # Check circuit breaker timeout
                if self._circuit_state == CircuitState.OPEN:
                    if self._should_test_circuit():
                        logger.info(
                            "Circuit breaker timeout reached, testing connection..."
                        )
                        self._circuit_state = CircuitState.HALF_OPEN
                        await self._flush_batch()
                    continue

                # Normal periodic flush
                current_time = asyncio.get_event_loop().time()
                if current_time - self._last_flush >= self.config.batch_interval:
                    await self._flush_batch()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}", exc_info=True)

    def _should_test_circuit(self) -> bool:
        """Check if enough time has passed to test the circuit."""
        if self._circuit_opened_at is None:
            return True
        return (
            time.time() - self._circuit_opened_at
        ) >= self.config.circuit_breaker_timeout

    async def _flush_batch(self, force: bool = False) -> None:
        """Flush the current batch to InfluxDB with circuit breaker."""
        # Check circuit state
        if self._circuit_state == CircuitState.OPEN and not force:
            logger.debug("Circuit breaker OPEN, skipping flush")
            return

        async with self._batch_lock:
            if not self._batch and not force:
                return

            if not self._batch:
                logger.debug("No data to flush")
                return

            # Take current batch and clear it
            points_to_write = list(self._batch)
            self._batch.clear()

        # Write points
        try:
            logger.debug(f"Flushing {len(points_to_write)} points to InfluxDB")

            # Write to InfluxDB
            if self._write_api:
                await self._write_api.write(
                    bucket=self.config.influxdb_bucket, record=points_to_write
                )

            # Success - update state
            self._consecutive_failures = 0
            self._circuit_state = CircuitState.CLOSED
            self._total_written += len(points_to_write)
            self._last_successful_write = datetime.now()
            self._last_flush = asyncio.get_event_loop().time()

            logger.debug(
                f"Successfully wrote {len(points_to_write)} points to InfluxDB"
            )

        except Exception as e:
            # Failure - update state
            self._consecutive_failures += 1
            self._last_failure = datetime.now()

            logger.error(
                f"Failed to write to InfluxDB (attempt {self._consecutive_failures}): "
                f"{self._sanitize_error(e)}"
            )

            # Restore points to batch (prepend to maintain order)
            async with self._batch_lock:
                # Check available space
                space_available = self.config.max_buffer_size - len(self._batch)
                if space_available >= len(points_to_write):
                    self._batch.extendleft(reversed(points_to_write))
                else:
                    # Keep only newest points that fit
                    to_keep = (
                        points_to_write[-space_available:]
                        if space_available > 0
                        else []
                    )
                    dropped = len(points_to_write) - len(to_keep)
                    self._total_dropped += dropped
                    logger.warning(f"Buffer overflow, dropping {dropped} points")
                    self._batch.extendleft(reversed(to_keep))

            # Check circuit breaker
            if (
                self._consecutive_failures >= self.config.circuit_breaker_threshold
                and self._circuit_state != CircuitState.OPEN
            ):
                self._circuit_state = CircuitState.OPEN
                self._circuit_opened_at = time.time()
                timeout = self.config.circuit_breaker_timeout
                failures = self._consecutive_failures
                logger.error(
                    f"Circuit breaker OPEN after {failures} failures. "
                    f"Will retry in {timeout}s"
                )

            # Exponential backoff
            backoff_time = min(
                self.config.batch_retry_interval
                * (2 ** (self._consecutive_failures - 1)),
                60,  # Max 1 minute
            )
            await asyncio.sleep(backoff_time)

    def _sanitize_error(self, error: Exception) -> str:
        """Sanitize error messages to avoid exposing sensitive data."""
        error_str = str(error)

        # Remove potential token exposure
        if self.config.influxdb_token in error_str:
            error_str = error_str.replace(self.config.influxdb_token, "***TOKEN***")

        # Remove URL with potential credentials
        if self.config.influxdb_url in error_str:
            error_str = error_str.replace(
                self.config.influxdb_url, self._sanitize_url(self.config.influxdb_url)
            )

        return error_str

    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL to remove any credentials."""
        # Simple sanitization - just show host
        if "://" in url:
            parts = url.split("://", 1)
            host = parts[1].split("/", 1)[0] if "/" in parts[1] else parts[1]
            return f"{parts[0]}://{host}/..."
        return url

    async def health_check(self) -> dict[str, Any]:
        """Perform health check and return status."""
        # Determine health status
        if self._circuit_state == CircuitState.OPEN:
            status = "unhealthy"
        elif len(self._batch) > self.config.max_buffer_size * 0.8:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "buffer_size": len(self._batch),
            "buffer_capacity": self.config.max_buffer_size,
            "circuit_breaker": self._circuit_state.value,
            "consecutive_failures": self._consecutive_failures,
            "total_written": self._total_written,
            "total_dropped": self._total_dropped,
            "last_write": (
                self._last_successful_write.isoformat()
                if self._last_successful_write
                else None
            ),
        }
