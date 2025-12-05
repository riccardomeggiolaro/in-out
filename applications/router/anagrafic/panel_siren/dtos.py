"""
Data Transfer Objects (DTOs) for Panel and Siren configuration.
"""

from pydantic import BaseModel, field_validator, Field
from typing import Optional, Any


class ConnectionConfig(BaseModel):
    """Connection parameters for devices."""

    ip: str = Field(..., description="IP address of the device")
    port: int = Field(..., description="Port number")
    timeout: float = Field(5.0, description="Connection timeout in seconds", gt=0.1)


class DeviceConfig(BaseModel):
    """
    Generic device configuration with adapter system.

    This model supports different adapter types with flexible configuration.
    """

    enabled: bool = Field(True, description="Whether the device is enabled")
    type: str = Field(..., description="Adapter type (e.g., tcp_custom, http_digest)")
    connection: ConnectionConfig = Field(..., description="Connection parameters")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Adapter-specific configuration"
    )

    @field_validator("type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> str:
        """Validate adapter type is supported."""
        from .adapters import AdapterFactory

        supported = AdapterFactory.get_supported_types()
        if v not in supported:
            raise ValueError(
                f"Invalid adapter type '{v}'. Supported types: {supported}"
            )
        return v


class PanelConfig(DeviceConfig):
    """
    Panel device configuration.

    Example for TCP custom (original protocol):
    {
        "enabled": true,
        "type": "tcp_custom",
        "connection": {"ip": "192.168.1.100", "port": 5000, "timeout": 5.0},
        "config": {
            "max_string_content": 3,  # Max WORDS (not chars!) in scrolling buffer
            "panel_id": 16,
            "duration": 90
        }
    }

    Example for TCP raw:
    {
        "enabled": true,
        "type": "tcp_raw",
        "connection": {"ip": "192.168.1.100", "port": 5000, "timeout": 5.0},
        "config": {
            "encoding": "utf-8",
            "line_ending": "\\r\\n",
            "wait_response": false
        }
    }

    Example for HTTP simple:
    {
        "enabled": true,
        "type": "http_simple",
        "connection": {"ip": "192.168.1.100", "port": 80, "timeout": 5.0},
        "config": {
            "endpoint": "http://192.168.1.100/display",
            "method": "POST",
            "query_param": "text"
        }
    }
    """

    pass


class SirenConfig(DeviceConfig):
    """
    Siren device configuration.

    Example for HTTP digest (original protocol):
    {
        "enabled": true,
        "type": "http_digest",
        "connection": {"ip": "100.100.100.101", "port": 80, "timeout": 5.0},
        "config": {
            "endpoint": "http://localhost",
            "method": "GET",
            "username": "marco",
            "password": "318101"
        }
    }

    Example for HTTP simple:
    {
        "enabled": true,
        "type": "http_simple",
        "connection": {"ip": "192.168.1.50", "port": 8080, "timeout": 5.0},
        "config": {
            "endpoint": "http://192.168.1.50:8080/buzzer",
            "method": "GET"
        }
    }

    Example for disabled:
    {
        "enabled": false,
        "type": "disabled",
        "connection": {"ip": "0.0.0.0", "port": 0, "timeout": 5.0},
        "config": {}
    }
    """

    pass


# Legacy DTOs for backward compatibility (deprecated)
class Configuration(BaseModel):
    """
    Legacy configuration model (deprecated).

    Use DeviceConfig instead.
    """

    ip: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: Optional[float] = 5
    endpoint: Optional[str] = None

    @field_validator("timeout")
    @classmethod
    def check_timeout(cls, v):
        if v <= 0.1:
            raise ValueError("Timeout need to be greater than 0.1")
        return v


class Panel(Configuration):
    """
    Legacy panel configuration (deprecated).

    Use PanelConfig instead.
    """

    max_string_content: int

    @field_validator("max_string_content")
    @classmethod
    def check_max_content(cls, v):
        if v <= 0:
            raise ValueError("Max string content need to be greater than 0")
        return v


class Siren(Configuration):
    """
    Legacy siren configuration (deprecated).

    Use SirenConfig instead.
    """

    pass
