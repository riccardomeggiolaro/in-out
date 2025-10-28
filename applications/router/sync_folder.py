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
from modules.md_sync_folder.dto import SyncFolderDTO
import modules.md_sync_folder.md_sync_folder as md_sync_folder

class SyncFolderRouter:
    def __init__(self):
        self.router = APIRouter()
        
        config = lb_config.g_config["app_api"]["sync_folder"]["remote_folder"]
        if config:
            status = md_sync_folder.module_sync_folder.create_remote_connection(config=SyncFolderDTO(**config), local_dir=lb_config.g_config["app_api"]["sync_folder"]["local_dir"], mount_point=lb_config.g_config["app_api"]["sync_folder"]["mount_point"])
            import libs.lb_log as lb_log
            lb_log.info(f"Sync Folder mounted at startup: {status}")

        # Aggiungi le rotte
        self.router.add_api_route('', self.getSyncFolder, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.SetSyncFolder, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.DeleteSyncFolder, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/test', self.TestSyncFolder, methods=['GET'], dependencies=[Depends(is_super_admin)])

    async def getSyncFolder(self):
        return lb_config.g_config["app_api"]["sync_folder"]

    async def SetSyncFolder(self, body: SyncFolderDTO):
        mounted = md_sync_folder.module_sync_folder.create_remote_connection(config=body, local_dir=lb_config.g_config["app_api"]["sync_folder"]["local_dir"], mount_point=lb_config.g_config["app_api"]["sync_folder"]["mount_point"])
        lb_config.g_config["app_api"]["sync_folder"]["remote_folder"] = body.dict()
        lb_config.saveconfig()
        return { 
                "mounted": mounted,
                "remote_folder": lb_config.g_config["app_api"]["sync_folder"]["remote_folder"]
            }

    async def DeleteSyncFolder(self):
        md_sync_folder.module_sync_folder.delete_remote_connection()
        lb_config.g_config["app_api"]["sync_folder"]["remote_folder"] = None
        lb_config.saveconfig()
        return { "deleted": True }
    
    async def TestSyncFolder(self):
        mounted = md_sync_folder.module_sync_folder.test_connection()
        return { "mounted": mounted }