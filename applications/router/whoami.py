from fastapi import APIRouter
import libs.lb_config as lb_config

class WhoAmIRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/whoami', self.getWhoAmI)
        
    async def getWhoAmI(self):
        """Restituisce informazioni sull'utente corrente (super admin)"""
        return {
            "program_name": lb_config.g_config["name"]
        }