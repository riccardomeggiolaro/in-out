"""
TCP Raw adapter for simple text-based TCP communication.

This adapter sends plain text messages over TCP without any special encoding.
"""

import asyncio
from typing import Optional

from .base import BaseAdapter, AdapterType


class TcpRawAdapter(BaseAdapter):
    """
    TCP adapter for raw text messages.

    Sends plain text over TCP connection. Useful for simple devices
    that accept text commands without special protocols.
    """

    def __init__(self, connection: dict, config: Optional[dict] = None):
        super().__init__(connection, config)
        self.encoding = self.config.get("encoding", "utf-8")
        self.line_ending = self.config.get("line_ending", "\r\n")
        self.wait_response = self.config.get("wait_response", False)
        self.response_bytes = self.config.get("response_bytes", 1024)

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.TCP_RAW

    async def send_message(self, message: Optional[str] = None) -> None:
        """
        Send a plain text message over TCP.

        Args:
            message: Text message to send (required)

        Raises:
            ValueError: If message is not provided
            ConnectionError: If communication fails
        """
        if not message:
            raise ValueError("Message is required for TCP raw adapter")

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port), timeout=self.timeout
            )

            # Send message with line ending
            data = f"{message}{self.line_ending}".encode(self.encoding)
            writer.write(data)
            await writer.drain()

            # Optionally wait for response
            if self.wait_response:
                response = await asyncio.wait_for(
                    reader.read(self.response_bytes), timeout=self.timeout
                )
                # Response is read but not returned (fire and forget style)

            writer.close()
            await writer.wait_closed()

        except asyncio.TimeoutError:
            raise ConnectionError(
                f"Host {self.ip}:{self.port} non raggiungibile (timeout)"
            )
        except ConnectionRefusedError:
            raise ConnectionRefusedError(
                f"Connection refused by {self.ip}:{self.port}"
            )
        except OSError as e:
            raise ConnectionError(f"Errore di rete con {self.ip}:{self.port}: {e}")
        except Exception as e:
            raise ConnectionError(f"Errore di rete con {self.ip}:{self.port}: {e}")
