from fastapi import APIRouter, HTTPException
import libs.lb_system as lb_system
import libs.lb_config as lb_config
from applications.router.anagrafic.panel_siren.functions.functions import send_panel_message, send_siren_message
from applications.router.anagrafic.panel_siren.dtos import Panel, Siren
from modules.md_database.functions.get_data_by_id import get_data_by_id
from typing import Optional

class PanelSirenRouter:
    def __init__(self):
        self.buffer = ""
        self.panel_siren_router = APIRouter()

        # Aggiungi le rotte
        self.panel_siren_router.add_api_route('/message/panel', self.sendMessagePanel, methods=["GET"])
        self.panel_siren_router.add_api_route('/cancel-message/panel', self.deleteMessagePanel, methods=["DELETE"])
        self.panel_siren_router.add_api_route('/call/siren', self.sendMessageSiren, methods=["GET"])
        self.panel_siren_router.add_api_route('/configuration/panel', self.getConfigurationPanel, methods=["GET"])
        self.panel_siren_router.add_api_route('/configuration/panel', self.setConfigurationPanel, methods=["PATCH"])
        self.panel_siren_router.add_api_route('/configuration/panel', self.deleteConfigurationPanel, methods=["DELETE"])
        self.panel_siren_router.add_api_route('/configuration/siren', self.getConfigurationSiren, methods=["GET"])
        self.panel_siren_router.add_api_route('/configuration/siren', self.setConfigurationSiren, methods=["PATCH"])
        self.panel_siren_router.add_api_route('/configuration/siren', self.deleteConfigurationSiren, methods=["DELETE"])

    def editBuffer(self, text: str):
        words = self.buffer.split()
        string = self.buffer
        n = lb_config.g_config["app_api"]["panel"]["max_string_content"] if lb_config.g_config["app_api"]["panel"]["max_string_content"] else 1
        new_buffer = string if n >= len(string) else ' '.join(string[-n:])
        self.buffer = new_buffer + text
        return self.buffer

    def undoBuffer(self, text: str):
        string = self.buffer
        if text in string:
            string = string.replace(text, '', 1)
        return string

    async def sendMessagePanel(self, text: str):
        old_buf = self.buffer
        try:
            buf = self.editBuffer(text)
            await send_panel_message(buf)
            return buf
        except Exception as e:
            self.buffer = old_buf
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def deleteMessagePanel(self, text: str):
        old_buf = self.buffer
        try:
            buf = self.undoBuffer(text)
            await send_panel_message(buf)
            return buf
        except Exception as e:
            self.buffer = old_buf
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
    
    async def sendMessageSiren(self):
        try:
            send_siren_message()
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def getConfigurationPanel(self):
        return lb_config.g_config["app_api"]["panel"]        
        
    async def setConfigurationPanel(self, configuration: Panel):
        try:
            lb_config.g_config["app_api"]["panel"] = configuration.dict()
            lb_config.saveconfig()
            return lb_config.g_config["app_api"]["panel"]
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
    
    async def deleteConfigurationPanel(self):
        for key in lb_config.g_config["app_api"]["panel"]:
            lb_config.g_config["app_api"]["panel"][key] = None
        lb_config.saveconfig()
        return lb_config.g_config["app_api"]["panel"]

    async def getConfigurationSiren(self):
        return lb_config.g_config["app_api"]["siren"]
    
    async def setConfigurationSiren(self, configuration: Siren):
        try:
            lb_config.g_config["app_api"]["siren"] = configuration.dict()
            lb_config.saveconfig()
            return lb_config.g_config["app_api"]["siren"]
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        
    async def deleteConfigurationSiren(self):
        for key in lb_config.g_config["app_api"]["siren"]:
            lb_config.g_config["app_api"]["siren"][key] = None
        lb_config.saveconfig()
        return lb_config.g_config["app_api"]["siren"]