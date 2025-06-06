from fastapi import APIRouter
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