"""
Adapters for Panel and Siren systems.

This package provides a flexible adapter system to support different
communication protocols and authentication methods for panel and siren devices.
"""

from .base import BaseAdapter, AdapterType, DisabledAdapter
from .factory import AdapterFactory
from .tcp_custom import TcpCustomAdapter
from .tcp_raw import TcpRawAdapter
from .http_adapters import (
    HttpSimpleAdapter,
    HttpBasicAdapter,
    HttpDigestAdapter,
    HttpBearerAdapter,
)

__all__ = [
    "BaseAdapter",
    "AdapterType",
    "DisabledAdapter",
    "AdapterFactory",
    "TcpCustomAdapter",
    "TcpRawAdapter",
    "HttpSimpleAdapter",
    "HttpBasicAdapter",
    "HttpDigestAdapter",
    "HttpBearerAdapter",
]
