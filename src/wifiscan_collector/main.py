"""Main application module.

This module contains the main application class that coordinates WiFi scanning,
data storage, and overall application lifecycle management.

The application follows these key principles:
- Async/await architecture for non-blocking operations
- Graceful shutdown with proper resource cleanup
- Comprehensive error handling and recovery
- Production-ready logging and monitoring
- Interface auto-detection and validation

Example:
    Running the application:
        config = Config()
        app = WifiScanCollector(config)
        await app.run()

    Or using the convenience function:
        run()  # Handles asyncio.run() automatically
"""

import asyncio
import logging
import signal
import sys

from .config import Config
from .scanner import WifiScanner
from .storage import InfluxDBStorage
from .utils import get_safe_config_dict
from .version import get_version_info

logger = logging.getLogger(__name__)


class WifiScanCollector:
    """Main application class for WiFi scanning and data collection.

    This class coordinates all aspects of the WiFi scanning application:
    - Configuration management
    - Interface discovery and validation
    - WiFi scanning operations
    - Data storage to InfluxDB
    - Signal handling and graceful shutdown
    - Statistics and monitoring

    The application is designed for long-running deployment with
    comprehensive error handling and recovery mechanisms.

    Attributes:
        config: Application configuration
        scanner: WiFi scanner instance
        storage: InfluxDB storage handler

    Example:
        config = Config()
        app = WifiScanCollector(config)
        await app.run()
    """

    def __init__(self, config: Config):
        """Initialize the application with configuration.

        Args:
            config: Validated configuration object
        """
        self.config = config
        self.scanner = WifiScanner(
            config.wireless_interface or "wlan0", config.scan_timeout
        )
        self.storage = InfluxDBStorage(config)
        self._running = True
        self._tasks: list[asyncio.Task] = []

    def _setup_logging(self) -> None:
        """Configure application logging.

        Sets up logging with appropriate format and level based on
        configuration. Logs are sent to stdout for container compatibility.
        """
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        logging.basicConfig(
            level=getattr(logging, self.config.log_level, logging.INFO),
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown.

        Handles SIGTERM and SIGINT signals to allow graceful shutdown
        when running in containers or receiving keyboard interrupts.
        """

        def signal_handler(signum: int) -> None:
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self._running = False

        # Handle signals in async-friendly way
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, _: signal_handler(s))

    def _format_uptime(self, seconds: int) -> str:
        """Format uptime seconds into human-readable string.

        Args:
            seconds: Total uptime in seconds

        Returns:
            Formatted uptime string (e.g., "2d 3h 45m", "1h 30m", "45s")
        """
        if seconds < 60:
            return f"{seconds}s"

        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"

        hours = minutes // 60
        remaining_minutes = minutes % 60
        if hours < 24:
            return f"{hours}h {remaining_minutes}m"

        days = hours // 24
        remaining_hours = hours % 24
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        else:
            return f"{days}d"

    async def run(self) -> None:
        """Main application run loop.

        This is the main entry point that:
        1. Sets up logging and signal handlers
        2. Discovers and validates wireless interfaces
        3. Initializes storage connection
        4. Runs the continuous scanning loop
        5. Handles graceful shutdown

        The scanning loop continues until a shutdown signal is received
        or an unrecoverable error occurs.

        Raises:
            SystemExit: If critical initialization fails
        """
        self._setup_logging()
        self._setup_signal_handlers()

        # Log version info
        version_info = get_version_info()
        logger.info(
            f"Starting WiFi Scanner Collector v{version_info['version']} "
            f"(built: {version_info['build_time']})"
        )

        # Log configuration with obfuscated sensitive values
        safe_config = get_safe_config_dict(self.config)
        logger.info("Configuration loaded:")
        for key, value in safe_config.items():
            logger.info(f"  {key}: {value}")

        # Discover and log available wireless interfaces
        logger.info("Discovering wireless interfaces...")
        available_interfaces = await WifiScanner.discover_wireless_interfaces()

        if not available_interfaces:
            logger.error("No wireless interfaces found. Please check your hardware.")
            sys.exit(1)

        logger.info(f"Found {len(available_interfaces)} wireless interface(s):")
        for iface, state in available_interfaces:
            details = await WifiScanner.get_interface_details(iface)
            if details:
                logger.info(f"  - {iface}: {state}")
                logger.info(f"    MAC: {details.get('mac', 'unknown')}")
                if details.get("type"):
                    logger.info(f"    Type: {details['type']}")
                if details.get("ssid"):
                    logger.info(f"    Connected to: {details['ssid']}")

        # Handle interface auto-detection if not specified
        if self.config.wireless_interface is None:
            selected_interface = WifiScanner.select_best_interface(available_interfaces)
            if selected_interface:
                logger.info(f"Auto-selected interface: {selected_interface}")
                self.config.wireless_interface = selected_interface
                # Recreate scanner with selected interface
                self.scanner = WifiScanner(
                    interface=selected_interface, scan_timeout=self.config.scan_timeout
                )
            else:
                logger.error("Could not auto-select a wireless interface.")
                sys.exit(1)
        else:
            # Verify specified interface exists
            interface_names = [iface for iface, _ in available_interfaces]
            if self.config.wireless_interface not in interface_names:
                iface_name = self.config.wireless_interface
                logger.error(
                    f"Specified interface '{iface_name}' not found. "
                    f"Available interfaces: {', '.join(interface_names)}"
                )
                sys.exit(1)
            logger.info(f"Using specified interface: {self.config.wireless_interface}")

        # Check interface before starting
        if not await self.scanner.check_interface():
            logger.error("Interface check failed. Exiting.")
            sys.exit(1)

        # Start storage
        try:
            await self.storage.start()
        except Exception as e:
            logger.error(f"Failed to start storage: {e}")
            sys.exit(1)

        consecutive_failures = 0
        last_status_log = 0.0

        # Track application start time for uptime calculation
        start_time = asyncio.get_event_loop().time()

        # Statistics for periodic logging
        scan_count = 0
        total_networks_found = 0
        scan_failures = 0

        try:
            while self._running:
                # Run scan
                scan_start = asyncio.get_event_loop().time()
                networks = await self.scanner.scan()
                scan_duration = asyncio.get_event_loop().time() - scan_start

                scan_count += 1

                if networks:
                    # Reset failure counter on successful scan
                    consecutive_failures = 0
                    total_networks_found += len(networks)

                    # Add to storage batch
                    await self.storage.add_networks(networks)

                    # Only log details at debug level
                    logger.debug(
                        f"Scan {scan_count} completed in {scan_duration:.2f}s, "
                        f"found {len(networks)} networks"
                    )
                else:
                    consecutive_failures += 1
                    scan_failures += 1
                    logger.warning(
                        f"Scan {scan_count} failed "
                        f"(consecutive failures: {consecutive_failures})"
                    )

                    # If we've failed too many times, check the interface again
                    if consecutive_failures >= self.config.max_retries:
                        logger.error("Max consecutive failures reached")
                        if not await self.scanner.check_interface():
                            logger.error(
                                "Interface check failed. Waiting before retry..."
                            )
                            await asyncio.sleep(self.config.retry_delay)
                        consecutive_failures = 0

                # Periodic status logging
                current_time = asyncio.get_event_loop().time()
                if (
                    self.config.status_log_interval > 0
                    and current_time - last_status_log
                    >= self.config.status_log_interval
                ):
                    avg_networks = (
                        total_networks_found / scan_count if scan_count > 0 else 0
                    )
                    success_rate = (
                        ((scan_count - scan_failures) / scan_count * 100)
                        if scan_count > 0
                        else 0
                    )

                    # Get storage stats
                    storage_health = await self.storage.health_check()

                    # Calculate uptime
                    uptime_seconds = int(current_time - start_time)
                    uptime_str = self._format_uptime(uptime_seconds)

                    logger.info(
                        f"Uptime: {uptime_str} | "
                        f"Scanner: {scan_count} scans, {success_rate:.1f}% success, "
                        f"{avg_networks:.1f} networks/scan | "
                        f"Storage: {storage_health['total_written']} written, "
                        f"{storage_health['buffer_size']} buffered, "
                        f"{storage_health['total_dropped']} dropped"
                    )
                    last_status_log = current_time

                # Calculate sleep time
                sleep_time = max(0.0, self.config.scan_interval - scan_duration)

                if sleep_time > 0 and self._running:
                    logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
                    try:
                        await asyncio.sleep(sleep_time)
                    except asyncio.CancelledError:
                        break
                elif self._running:
                    logger.warning(
                        f"Scan took {scan_duration:.2f}s, "
                        f"longer than interval {self.config.scan_interval}s"
                    )

        finally:
            # Cleanup
            logger.info("Shutting down...")
            await self.storage.stop()
            logger.info("WiFi scanner stopped")


async def main() -> None:
    """Main entry point for the application.

    Loads configuration, creates the application instance, and runs it.
    Handles keyboard interrupts gracefully and logs fatal errors.

    This function is the async entry point that:
    1. Loads configuration from environment variables
    2. Creates WifiScanCollector instance
    3. Runs the application
    4. Handles shutdown scenarios

    Raises:
        SystemExit: On fatal errors
    """
    try:
        # Load configuration from environment variables
        config = Config()  # type: ignore[call-arg]

        # Create and run application
        app = WifiScanCollector(config)
        await app.run()

    except KeyboardInterrupt:
        logger.info("Shutdown requested...exiting")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def run() -> None:
    """Run the application with asyncio.

    This is the synchronous entry point that handles the asyncio event loop.
    It's designed to be called from the command line or other synchronous contexts.

    Example:
        from wifiscan_collector.main import run
        run()  # Starts the application
    """
    asyncio.run(main())
