"""
HTTP adapters for Panel and Siren communication.

Supports various HTTP methods and authentication mechanisms.
"""

import httpx
from typing import Optional, Literal

from .base import BaseAdapter, AdapterType


class HttpSimpleAdapter(BaseAdapter):
    """
    Simple HTTP adapter without authentication.

    Sends HTTP requests to the specified endpoint without any credentials.
    """

    def __init__(self, connection: dict, config: Optional[dict] = None):
        super().__init__(connection, config)
        self.endpoint = self.config.get("endpoint", "")
        self.method = self.config.get("method", "GET").upper()
        self.headers = self.config.get("headers", {})
        self.body_param = self.config.get("body_param", "message")
        self.query_param = self.config.get("query_param", None)

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.HTTP_SIMPLE

    def validate_config(self) -> bool:
        """Validate HTTP simple configuration."""
        super().validate_config()
        if not self.endpoint:
            raise ValueError("Endpoint URL is required for HTTP simple adapter")
        if self.method not in ["GET", "POST", "PUT", "PATCH"]:
            raise ValueError(f"Invalid HTTP method: {self.method}")
        return True

    async def send_message(self, message: Optional[str] = None) -> None:
        """
        Send HTTP request without authentication.

        Args:
            message: Optional message (can be sent as query param or body)

        Raises:
            ConnectionError: If HTTP request fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                json_data = None

                # Add message to request if provided
                if message and self.query_param:
                    params[self.query_param] = message
                elif message and self.method in ["POST", "PUT", "PATCH"]:
                    json_data = {self.body_param: message}

                response = await client.request(
                    method=self.method,
                    url=self.endpoint,
                    params=params if params else None,
                    json=json_data,
                    headers=self.headers,
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Errore HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Errore di richiesta HTTP: {e}")
        except Exception as e:
            raise ConnectionError(f"Errore sconosciuto durante la richiesta HTTP: {e}")


class HttpBasicAdapter(BaseAdapter):
    """
    HTTP adapter with Basic authentication.

    Sends HTTP requests using HTTP Basic Auth (username:password in base64).
    """

    def __init__(self, connection: dict, config: Optional[dict] = None):
        super().__init__(connection, config)
        self.endpoint = self.config.get("endpoint", "")
        self.method = self.config.get("method", "GET").upper()
        self.username = self.config.get("username", "")
        self.password = self.config.get("password", "")
        self.headers = self.config.get("headers", {})
        self.body_param = self.config.get("body_param", "message")
        self.query_param = self.config.get("query_param", None)

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.HTTP_BASIC

    def validate_config(self) -> bool:
        """Validate HTTP basic auth configuration."""
        super().validate_config()
        if not self.endpoint:
            raise ValueError("Endpoint URL is required for HTTP basic adapter")
        if not self.username or not self.password:
            raise ValueError("Username and password are required for HTTP basic auth")
        return True

    async def send_message(self, message: Optional[str] = None) -> None:
        """
        Send HTTP request with Basic authentication.

        Args:
            message: Optional message

        Raises:
            ConnectionError: If HTTP request fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                json_data = None

                if message and self.query_param:
                    params[self.query_param] = message
                elif message and self.method in ["POST", "PUT", "PATCH"]:
                    json_data = {self.body_param: message}

                response = await client.request(
                    method=self.method,
                    url=self.endpoint,
                    params=params if params else None,
                    json=json_data,
                    headers=self.headers,
                    auth=(self.username, self.password),
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Errore HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Errore di richiesta HTTP: {e}")
        except Exception as e:
            raise ConnectionError(f"Errore sconosciuto durante la richiesta HTTP: {e}")


class HttpDigestAdapter(BaseAdapter):
    """
    HTTP adapter with Digest authentication.

    Sends HTTP requests using HTTP Digest Auth (more secure than Basic).
    This is the original siren adapter.
    """

    def __init__(self, connection: dict, config: Optional[dict] = None):
        super().__init__(connection, config)
        self.endpoint = self.config.get("endpoint", "")
        self.method = self.config.get("method", "GET").upper()
        self.username = self.config.get("username", "")
        self.password = self.config.get("password", "")
        self.headers = self.config.get("headers", {})
        self.body_param = self.config.get("body_param", "message")
        self.query_param = self.config.get("query_param", None)

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.HTTP_DIGEST

    def validate_config(self) -> bool:
        """Validate HTTP digest auth configuration."""
        super().validate_config()
        if not self.endpoint:
            raise ValueError("Endpoint URL is required for HTTP digest adapter")
        if not self.username or not self.password:
            raise ValueError("Username and password are required for HTTP digest auth")
        return True

    async def send_message(self, message: Optional[str] = None) -> None:
        """
        Send HTTP request with Digest authentication.

        Args:
            message: Optional message

        Raises:
            ConnectionError: If HTTP request fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                json_data = None

                if message and self.query_param:
                    params[self.query_param] = message
                elif message and self.method in ["POST", "PUT", "PATCH"]:
                    json_data = {self.body_param: message}

                response = await client.request(
                    method=self.method,
                    url=self.endpoint,
                    params=params if params else None,
                    json=json_data,
                    headers=self.headers,
                    auth=httpx.DigestAuth(self.username, self.password),
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Errore HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Errore di richiesta HTTP: {e}")
        except Exception as e:
            raise ConnectionError(f"Errore sconosciuto durante la richiesta HTTP: {e}")


class HttpBearerAdapter(BaseAdapter):
    """
    HTTP adapter with Bearer token authentication.

    Sends HTTP requests with Bearer token in Authorization header.
    """

    def __init__(self, connection: dict, config: Optional[dict] = None):
        super().__init__(connection, config)
        self.endpoint = self.config.get("endpoint", "")
        self.method = self.config.get("method", "GET").upper()
        self.token = self.config.get("token", "")
        self.headers = self.config.get("headers", {})
        self.body_param = self.config.get("body_param", "message")
        self.query_param = self.config.get("query_param", None)

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.HTTP_BEARER

    def validate_config(self) -> bool:
        """Validate HTTP bearer token configuration."""
        super().validate_config()
        if not self.endpoint:
            raise ValueError("Endpoint URL is required for HTTP bearer adapter")
        if not self.token:
            raise ValueError("Bearer token is required")
        return True

    async def send_message(self, message: Optional[str] = None) -> None:
        """
        Send HTTP request with Bearer token authentication.

        Args:
            message: Optional message

        Raises:
            ConnectionError: If HTTP request fails
        """
        try:
            # Add Bearer token to headers
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {self.token}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                json_data = None

                if message and self.query_param:
                    params[self.query_param] = message
                elif message and self.method in ["POST", "PUT", "PATCH"]:
                    json_data = {self.body_param: message}

                response = await client.request(
                    method=self.method,
                    url=self.endpoint,
                    params=params if params else None,
                    json=json_data,
                    headers=headers,
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Errore HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Errore di richiesta HTTP: {e}")
        except Exception as e:
            raise ConnectionError(f"Errore sconosciuto durante la richiesta HTTP: {e}")
