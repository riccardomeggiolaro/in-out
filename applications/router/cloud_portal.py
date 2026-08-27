from fastapi import APIRouter, Depends
from applications.middleware.super_admin import is_super_admin
import libs.lb_config as lb_config
import modules.md_cloud_portal.md_cloud_portal as md_cloud_portal
from modules.md_cloud_portal.dto import CloudPortalDTO

class CloudPortalRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('', self.getCloudPortal, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.setCloudPortal, methods=['PUT'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/test', self.testCloudPortal, methods=['GET'], dependencies=[Depends(is_super_admin)])

    async def getCloudPortal(self):
        config = lb_config.g_config["app_api"].get("cloud_portal") or CloudPortalDTO().dict()
        # Non esporre mai la api key per intero nella risposta
        config = dict(config)
        if config.get("api_key"):
            config["api_key"] = config["api_key"][:4] + "..." if len(config["api_key"]) > 4 else "***"
        return config

    async def setCloudPortal(self, body: CloudPortalDTO):
        lb_config.g_config["app_api"]["cloud_portal"] = body.dict()
        lb_config.saveconfig()
        md_cloud_portal.module_cloud_portal.update_config(body)
        return { "saved": True }

    async def testCloudPortal(self):
        ok, detail = md_cloud_portal.module_cloud_portal.test_connection()
        return { "connected": ok, "detail": detail }
