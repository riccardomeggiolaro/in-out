from fastapi import APIRouter, HTTPException
import libs.lb_system as lb_system
import libs.lb_config as lb_config
from applications.router.panel_siren.functions.functions import send_panel_message, send_siren_message
from applications.router.panel_siren.dtos import Panel, Siren
from modules.md_database.functions.get_data_by_id import get_data_by_id
from typing import Optional

class PanelSirenRouter:
    def __init__(self):
        self.buffer = ""

        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/message/panel', self.sendMessagePanel, methods=["GET"])
        self.router.add_api_route('/delete/message/panel', self.deleteMessagePanel, methods=["DELETE"])
        self.router.add_api_route('/call/siren', self.sendMessageSiren, methods=["GET"])
        self.router.add_api_route('/panel-siren', self.sendMessageAll, methods=["GET"])
        self.router.add_api_route('/configuration/panel', self.setConfigurationPanel, methods=["PATCH"])
        self.router.add_api_route('/configuration/panel', self.deleteConfigurationPanel, methods=["DELETE"])
        self.router.add_api_route('/configuration/siren', self.setConfigurationSiren, methods=["PATCH"])
        self.router.add_api_route('/configuration/siren', self.deleteConfigurationSiren, methods=["DELETE"])

    def editBuffer(self, text: str):
        words = self.buffer.split()
        string = self.buffer
        n = lb_config.g_config["app_api"]["panel"]["max_string_content"] if lb_config.g_config["app_api"]["panel"]["max_string_content"] else 1
        new_buffer = string if n >= len(stringa) else ' '.join(stringa[-n:])
        self.buffer = new_buffer + text
        return self.buffer

    def undoBuffer(self, text: str):
        if text in self.buffer:
            self.buffer = self.buffer.replace(text, '', 1)
        return self.buffer

    async def sendMessagePanel(self, idReservation: Optional[int] = None, text: Optional[str] = None):
        try:
            data = text
            if idReservation:
                reservation = get_data_by_id("reservation", idReservation)
                data = reservation["vehicle"]["plate"]
            if not data:
                raise HTTPException(status_code=400, detail="Need something data for sending panel")
            edit_buffer = edit_buffer(data)
            send_panel_message(edit_buffer)
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def deleteMessagePanel(self, idReservation: Optional[int] = None, text: Optional[str] = None):
        try:
            data = text
            if idReservation:
                reservation = get_data_by_id("reservation", idReservation)
                data = reservation["vehicle"]["plate"]
            if not data:
                raise HTTPException(status_code=400, detail="Need something data for sending panel")
            undo_buffer = undo_buffer(data)
            send_panel_message(undo_buffer)
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
    
    async def sendMessageSiren(self, idReservation: Optional[int] = None, text: Optional[str] = None):
        try:
            send_siren_message()
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
    
    async def sendMessageAll(self, idReservation: Optional[int] = None, text: Optional[str] = None):
        try:
            await self.sendMessagePanel(idReservation, text)
            await self.sendMessageSiren(idReservation, text)
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        
    async def setConfigurationPanel(self, configuration: Panel):
        try:
            lb_config.g_config["app_api"]["panel"] = configuration.dict()
            lb_config.saveconfig()
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
    
    async def deleteConfigurationPanel(self):
        for key in lb_config.g_config["app_api"]["panel"]:
            lb_config.g_config["app_api"]["panel"][key] = None
        lb_config.saveconfig()
    
    async def setConfigurationSiren(self, configuration: Siren):
        try:
            lb_config.g_config["app_api"]["siren"] = configuration.dict()
            lb_config.saveconfig()
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        
    async def deleteConfigurationSiren(self):
        for key in lb_config.g_config["app_api"]["siren"]:
            lb_config.g_config["app_api"]["siren"][key] = None
        lb_config.saveconfig()