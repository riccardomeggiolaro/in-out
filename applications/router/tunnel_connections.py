from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Union
import libs.lb_log as lb_log
from libs.lb_database import VehicleDTO, SocialReasonDTO, MaterialDTO, filter_data, add_data, update_data, delete_data, delete_all_data, load_records_into_db, required_columns, required_dtos
import pandas as pd
import numpy as np
from applications.utils.utils import get_query_params
import libs.lb_config as lb_config
import modules.md_tunnel_connections.md_tunnel_connections as md_tunnel_connections
from modules.md_tunnel_connections.dto import SshClientConnectionDTO

class TunnelConnectionsRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('/ssh-reverse-tunneling', self.getSshReverseTunneling, methods=['GET'])        
        self.router.add_api_route('/ssh-reverse-tunneling', self.setSshReverseTunneling, methods=['PATCH'])
        self.router.add_api_route('/ssh-reverse-tunneling', self.deleteSshReverseTunneling, methods=['DELETE'])

    async def getSshReverseTunneling(self):
        return md_tunnel_connections.tunnel_connections.getSshReverseTunneling()
    
    async def setSshReverseTunneling(self, ssh_client: SshClientConnectionDTO):
        return md_tunnel_connections.tunnel_connections.setSshReverseTunneling()
    
    async def deleteSshReverseTunneling(self):
        return md_tunnel_connections.tunnel_connections.deleteSshReverseTunneling()