from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from applications.middleware.super_admin import is_super_admin
from fastapi.responses import StreamingResponse
import libs.lb_system as lb_system
import libs.lb_config as lb_config
from fastapi.responses import FileResponse
import os
from libs.lb_printer import printer
from applications.utils.utils_report import generate_html_report
from io import BytesIO
import shutil
from pathlib import Path
from collections import defaultdict
from pydantic import BaseModel, validator, field_validator, ValidationInfo
import re
import json
import zipfile
import os
import json
import zipfile
import asyncio
import aiofiles
import time
from io import BytesIO
from fastapi import UploadFile, HTTPException
from modules.md_sync_folder.dto import SyncFolderDTO
from libs.lb_sync_folder import mount_remote

class SyncFolderRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/sync_folder', self.getSyncFolder, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/sync_folder', self.SetSyncFolder, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/sync_folder', self.DeleteSyncFolder, methods=['DELETE'], dependencies=[Depends(is_super_admin)])

    async def getSyncFolder(self):
        return lb_config.g_config["app_api"]["sync_folder"]

    async def SetSyncFolder(self, body: SyncFolderDTO):
        lb_config.g_config["app_api"]["sync_folder"] = body.dict()
        lb_config.saveconfig()
        status = mount_remote(body.dict())
        return { "status": status }

    async def DeleteSyncFolder(self):
        lb_config.g_config["app_api"]["sync_folder"] = None
        lb_config.saveconfig()
        return { "deleted": True }