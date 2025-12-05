"""
TCP Custom adapter for Panel with binary protocol.

This adapter implements the custom binary protocol used by specific panel hardware.
"""

import asyncio
from typing import Optional

from .base import BaseAdapter, AdapterType


class PanelMessage:
    """Build custom binary messages for panel hardware."""

    def __init__(self, panel_id: int, duration: int = 0x5A):
        self.panel_id = panel_id
        self.duration = duration
        self.data = []

    def build_message(self, msg: str) -> bytes:
        """
        Build a binary message packet for the panel.

        Args:
            msg: Text message to display

        Returns:
            Binary packet ready to send
        """
        self.data.clear()
        self.data.extend([0xFF, 0xFF, 0xFF, 0xFF])
        self.data.extend([0, 0])  # Placeholder for length
        self.data.extend([0, 0, 0x68, 0x32, 0x10])  # Fixed bytes
        self.data.extend([0x7B, 0])
        self.data.extend([0, 0])  # Placeholder for CC length
        self.data.extend([0, 0, 2, 0, 0, 0, 0, 0, 3])  # More fixed bytes

        message_bytes = []
        for char in msg:
            self.data.extend([0x12, 0x00, ord(char)])
            message_bytes.extend([0x12, 0x00, ord(char)])

        self.data.extend([0, 0, 0])  # Fixed 3 bytes after message

        data_length = len(self.data) - 6
        self.data[5] = (data_length >> 8) & 0xFF
        self.data[4] = data_length & 0xFF

        string_length = (len(msg) + 1) * 3 + 7
        self.data[13] = string_length

        self.data[10] = self.panel_id
        self.data[22] = (self.duration >> 8) & 0xFF
        self.data[23] = self.duration & 0xFF

        checksum = sum(self.data[8:]) & 0xFFFF
        self.data.append(checksum & 0xFF)
        self.data.append((checksum >> 8) & 0xFF)

        return bytes(self.data)


class TcpCustomAdapter(BaseAdapter):
    """
    TCP adapter with custom binary protocol.

    This is the original panel protocol that uses a specific binary message format.
    """

    def __init__(self, connection: dict, config: Optional[dict] = None):
        super().__init__(connection, config)
        self.panel_id = self.config.get("panel_id", 0x10)
        self.duration = self.config.get("duration", 0x5A)

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.TCP_CUSTOM

    async def send_message(self, message: Optional[str] = None) -> None:
        """
        Send a message to the panel using the custom binary protocol.

        Args:
            message: Text message to display on panel

        Raises:
            ValueError: If message is not provided
            ConnectionError: If communication fails
        """
        if not message:
            raise ValueError("Message is required for TCP custom adapter")

        panel = PanelMessage(panel_id=self.panel_id, duration=self.duration)
        packet = panel.build_message(message)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port), timeout=self.timeout
            )

            writer.write(packet)
            await writer.drain()

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
