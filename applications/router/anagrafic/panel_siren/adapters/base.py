"""
Base adapter class for Panel and Siren communication.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional


class AdapterType(str, Enum):
    """Supported adapter types."""

    DISABLED = "disabled"
    TCP_CUSTOM = "tcp_custom"
    TCP_RAW = "tcp_raw"
    HTTP_SIMPLE = "http_simple"
    HTTP_BASIC = "http_basic"
    HTTP_DIGEST = "http_digest"
    HTTP_BEARER = "http_bearer"


class BaseAdapter(ABC):
    """
    Base class for all panel and siren adapters.

    Each adapter implements a specific communication protocol.
    """

    def __init__(self, connection: dict[str, Any], config: Optional[dict[str, Any]] = None):
        """
        Initialize the adapter.

        Args:
            connection: Connection parameters (ip, port, timeout, etc.)
            config: Additional configuration specific to the adapter type
        """
        self.connection = connection
        self.config = config or {}
        self.ip = connection.get("ip")
        self.port = connection.get("port")
        self.timeout = connection.get("timeout", 5.0)

    @abstractmethod
    async def send_message(self, message: Optional[str] = None) -> None:
        """
        Send a message to the device.

        Args:
            message: Message to send (optional, depends on adapter type)

        Raises:
            Exception: If communication fails
        """
        pass

    @property
    @abstractmethod
    def adapter_type(self) -> AdapterType:
        """Return the adapter type."""
        pass

    def validate_config(self) -> bool:
        """
        Validate that all required configuration parameters are present.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If required parameters are missing
        """
        if not self.ip:
            raise ValueError("IP address is required")
        if not self.port:
            raise ValueError("Port is required")
        if self.timeout <= 0.1:
            raise ValueError("Timeout must be greater than 0.1 seconds")
        return True


class DisabledAdapter(BaseAdapter):
    """Adapter for disabled devices (no-op)."""

    async def send_message(self, message: Optional[str] = None) -> None:
        """Does nothing - device is disabled."""
        pass

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.DISABLED

    def validate_config(self) -> bool:
        """No validation needed for disabled adapter."""
        return True
