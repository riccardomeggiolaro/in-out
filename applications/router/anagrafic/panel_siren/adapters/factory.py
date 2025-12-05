"""
Factory for creating adapter instances based on configuration.
"""

from typing import Optional

from .base import BaseAdapter, AdapterType, DisabledAdapter
from .tcp_custom import TcpCustomAdapter
from .tcp_raw import TcpRawAdapter
from .http_adapters import (
    HttpSimpleAdapter,
    HttpBasicAdapter,
    HttpDigestAdapter,
    HttpBearerAdapter,
)


class AdapterFactory:
    """
    Factory for creating adapter instances.

    Creates the appropriate adapter based on the configured type.
    """

    # Mapping of adapter types to adapter classes
    _ADAPTER_MAP = {
        AdapterType.DISABLED: DisabledAdapter,
        AdapterType.TCP_CUSTOM: TcpCustomAdapter,
        AdapterType.TCP_RAW: TcpRawAdapter,
        AdapterType.HTTP_SIMPLE: HttpSimpleAdapter,
        AdapterType.HTTP_BASIC: HttpBasicAdapter,
        AdapterType.HTTP_DIGEST: HttpDigestAdapter,
        AdapterType.HTTP_BEARER: HttpBearerAdapter,
    }

    @classmethod
    def create_adapter(
        cls,
        adapter_type: str,
        connection: dict,
        config: Optional[dict] = None,
        validate: bool = True,
    ) -> BaseAdapter:
        """
        Create an adapter instance.

        Args:
            adapter_type: Type of adapter to create (e.g., "tcp_custom", "http_digest")
            connection: Connection parameters (ip, port, timeout)
            config: Additional configuration specific to the adapter type
            validate: Whether to validate the configuration (default: True)

        Returns:
            An instance of the appropriate adapter

        Raises:
            ValueError: If adapter type is unknown or configuration is invalid
        """
        try:
            adapter_enum = AdapterType(adapter_type)
        except ValueError:
            raise ValueError(
                f"Unknown adapter type: {adapter_type}. "
                f"Valid types: {[t.value for t in AdapterType]}"
            )

        adapter_class = cls._ADAPTER_MAP.get(adapter_enum)
        if not adapter_class:
            raise ValueError(f"No adapter implementation for type: {adapter_type}")

        adapter = adapter_class(connection=connection, config=config)

        if validate:
            adapter.validate_config()

        return adapter

    @classmethod
    def create_from_config(cls, device_config: dict, validate: bool = True) -> BaseAdapter:
        """
        Create an adapter from a device configuration dictionary.

        Expected config format:
        {
            "enabled": true,
            "type": "tcp_custom",
            "connection": {"ip": "...", "port": 5000, "timeout": 5.0},
            "config": {...}
        }

        Args:
            device_config: Device configuration dictionary
            validate: Whether to validate the configuration (default: True)

        Returns:
            An instance of the appropriate adapter

        Raises:
            ValueError: If configuration is invalid
        """
        # Check if device is disabled
        if not device_config.get("enabled", True):
            return DisabledAdapter(connection={}, config={})

        adapter_type = device_config.get("type")
        if not adapter_type:
            raise ValueError("Device type is required in configuration")

        connection = device_config.get("connection", {})
        config = device_config.get("config", {})

        return cls.create_adapter(
            adapter_type=adapter_type,
            connection=connection,
            config=config,
            validate=validate,
        )

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        Get a list of all supported adapter types.

        Returns:
            List of adapter type strings
        """
        return [t.value for t in AdapterType]
