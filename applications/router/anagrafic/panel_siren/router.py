"""
Panel and Siren router with flexible adapter system.
"""

from fastapi import APIRouter, HTTPException
import libs.lb_config as lb_config
from applications.router.anagrafic.panel_siren.adapters import AdapterFactory
from applications.router.anagrafic.panel_siren.dtos import (
    PanelConfig,
    SirenConfig,
    Panel,
    Siren,
)


class PanelSirenRouter:
    """
    Router for Panel and Siren endpoints.

    Provides flexible adapter-based communication for various panel and siren devices.
    """

    def __init__(self):
        self.buffer = ""
        self.panel_siren_router = APIRouter()

        # Panel adapter (initialized lazily)
        self._panel_adapter = None
        # Siren adapter (initialized lazily)
        self._siren_adapter = None

        # Add routes
        self.panel_siren_router.add_api_route(
            "/message/panel", self.sendMessagePanel, methods=["GET"]
        )
        self.panel_siren_router.add_api_route(
            "/cancel-message/panel", self.deleteMessagePanel, methods=["DELETE"]
        )
        self.panel_siren_router.add_api_route(
            "/call/siren", self.sendMessageSiren, methods=["GET"]
        )
        self.panel_siren_router.add_api_route(
            "/configuration/panel", self.getConfigurationPanel, methods=["GET"]
        )
        self.panel_siren_router.add_api_route(
            "/configuration/panel", self.setConfigurationPanel, methods=["PATCH"]
        )
        self.panel_siren_router.add_api_route(
            "/configuration/panel", self.deleteConfigurationPanel, methods=["DELETE"]
        )
        self.panel_siren_router.add_api_route(
            "/configuration/siren", self.getConfigurationSiren, methods=["GET"]
        )
        self.panel_siren_router.add_api_route(
            "/configuration/siren", self.setConfigurationSiren, methods=["PATCH"]
        )
        self.panel_siren_router.add_api_route(
            "/configuration/siren", self.deleteConfigurationSiren, methods=["DELETE"]
        )

    def _get_panel_adapter(self):
        """Get or create panel adapter from configuration."""
        try:
            panel_config = lb_config.g_config["app_api"].get("panel", {})
            if not panel_config:
                # Default disabled adapter if not configured
                return AdapterFactory.create_from_config(
                    {"enabled": False, "type": "disabled", "connection": {}, "config": {}},
                    validate=False,
                )
            return AdapterFactory.create_from_config(panel_config, validate=True)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Invalid panel configuration: {str(e)}"
            )

    def _get_siren_adapter(self):
        """Get or create siren adapter from configuration."""
        try:
            siren_config = lb_config.g_config["app_api"].get("siren", {})
            if not siren_config:
                # Default disabled adapter if not configured
                return AdapterFactory.create_from_config(
                    {"enabled": False, "type": "disabled", "connection": {}, "config": {}},
                    validate=False,
                )
            return AdapterFactory.create_from_config(siren_config, validate=True)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Invalid siren configuration: {str(e)}"
            )

    def _get_max_string_content(self) -> int:
        """Get max string content from panel configuration."""
        panel_config = lb_config.g_config["app_api"].get("panel", {})
        config = panel_config.get("config", {})
        return config.get("max_string_content", 100)  # Default to 100

    def editBuffer(self, text: str) -> str:
        """
        Add text to buffer respecting max_string_content limit.

        Args:
            text: Text to add to buffer

        Returns:
            Updated buffer content
        """
        max_content = self._get_max_string_content()
        new_buffer = self.buffer + " " + text if self.buffer else text

        # Trim buffer if exceeds max_string_content
        if len(new_buffer) > max_content:
            # Keep only the last max_content characters
            new_buffer = new_buffer[-max_content:].lstrip()

        self.buffer = new_buffer
        return self.buffer

    def undoBuffer(self, text: str) -> str:
        """
        Remove text from buffer (first occurrence).

        Args:
            text: Text to remove from buffer

        Returns:
            Updated buffer content
        """
        if text in self.buffer:
            self.buffer = self.buffer.replace(text, "", 1).strip()
        return self.buffer

    async def sendMessagePanel(self, text: str):
        """
        Send message to panel display.

        Args:
            text: Text to add to panel display

        Returns:
            Current buffer content

        Raises:
            HTTPException: If sending message fails
        """
        old_buf = self.buffer
        try:
            buf = self.editBuffer(text)
            adapter = self._get_panel_adapter()
            await adapter.send_message(buf)
            return {"buffer": buf, "success": True}
        except Exception as e:
            self.buffer = old_buf
            status_code = getattr(e, "status_code", 500)
            detail = getattr(e, "detail", str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def deleteMessagePanel(self, text: str):
        """
        Remove message from panel display.

        Args:
            text: Text to remove from panel display

        Returns:
            Current buffer content

        Raises:
            HTTPException: If removing message fails
        """
        old_buf = self.buffer
        try:
            buf = self.undoBuffer(text)
            adapter = self._get_panel_adapter()
            await adapter.send_message(buf)
            return {"buffer": buf, "success": True}
        except Exception as e:
            self.buffer = old_buf
            status_code = getattr(e, "status_code", 500)
            detail = getattr(e, "detail", str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def sendMessageSiren(self):
        """
        Trigger siren activation.

        Returns:
            Success status

        Raises:
            HTTPException: If triggering siren fails
        """
        try:
            adapter = self._get_siren_adapter()
            await adapter.send_message()
            return {"success": True}
        except Exception as e:
            status_code = getattr(e, "status_code", 500)
            detail = getattr(e, "detail", str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def getConfigurationPanel(self):
        """Get current panel configuration."""
        return lb_config.g_config["app_api"].get("panel", {})

    async def setConfigurationPanel(self, configuration: PanelConfig):
        """
        Set panel configuration.

        Args:
            configuration: New panel configuration

        Returns:
            Updated configuration

        Raises:
            HTTPException: If configuration update fails
        """
        try:
            # Validate configuration by creating adapter
            AdapterFactory.create_from_config(configuration.model_dump(), validate=True)

            # Save configuration
            lb_config.g_config["app_api"]["panel"] = configuration.model_dump()
            lb_config.saveconfig()

            # Reset adapter to use new configuration
            self._panel_adapter = None

            return lb_config.g_config["app_api"]["panel"]
        except Exception as e:
            status_code = getattr(e, "status_code", 400)
            detail = getattr(e, "detail", str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setConfigurationPanelLegacy(self, configuration: Panel):
        """
        Set panel configuration (legacy format).

        This endpoint maintains backward compatibility with the old configuration format.

        Args:
            configuration: Legacy panel configuration

        Returns:
            Updated configuration

        Raises:
            HTTPException: If configuration update fails
        """
        try:
            lb_config.g_config["app_api"]["panel"] = configuration.model_dump()
            lb_config.saveconfig()
            self._panel_adapter = None
            return lb_config.g_config["app_api"]["panel"]
        except Exception as e:
            status_code = getattr(e, "status_code", 400)
            detail = getattr(e, "detail", str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def deleteConfigurationPanel(self):
        """Delete panel configuration (set to disabled)."""
        lb_config.g_config["app_api"]["panel"] = {
            "enabled": False,
            "type": "disabled",
            "connection": {"ip": "0.0.0.0", "port": 0, "timeout": 5.0},
            "config": {},
        }
        lb_config.saveconfig()
        self._panel_adapter = None
        return lb_config.g_config["app_api"]["panel"]

    async def getConfigurationSiren(self):
        """Get current siren configuration."""
        return lb_config.g_config["app_api"].get("siren", {})

    async def setConfigurationSiren(self, configuration: SirenConfig):
        """
        Set siren configuration.

        Args:
            configuration: New siren configuration

        Returns:
            Updated configuration

        Raises:
            HTTPException: If configuration update fails
        """
        try:
            # Validate configuration by creating adapter
            AdapterFactory.create_from_config(configuration.model_dump(), validate=True)

            # Save configuration
            lb_config.g_config["app_api"]["siren"] = configuration.model_dump()
            lb_config.saveconfig()

            # Reset adapter to use new configuration
            self._siren_adapter = None

            return lb_config.g_config["app_api"]["siren"]
        except Exception as e:
            status_code = getattr(e, "status_code", 400)
            detail = getattr(e, "detail", str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setConfigurationSirenLegacy(self, configuration: Siren):
        """
        Set siren configuration (legacy format).

        This endpoint maintains backward compatibility with the old configuration format.

        Args:
            configuration: Legacy siren configuration

        Returns:
            Updated configuration

        Raises:
            HTTPException: If configuration update fails
        """
        try:
            lb_config.g_config["app_api"]["siren"] = configuration.model_dump()
            lb_config.saveconfig()
            self._siren_adapter = None
            return lb_config.g_config["app_api"]["siren"]
        except Exception as e:
            status_code = getattr(e, "status_code", 400)
            detail = getattr(e, "detail", str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def deleteConfigurationSiren(self):
        """Delete siren configuration (set to disabled)."""
        lb_config.g_config["app_api"]["siren"] = {
            "enabled": False,
            "type": "disabled",
            "connection": {"ip": "0.0.0.0", "port": 0, "timeout": 5.0},
            "config": {},
        }
        lb_config.saveconfig()
        self._siren_adapter = None
        return lb_config.g_config["app_api"]["siren"]
