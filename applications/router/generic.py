from fastapi import APIRouter, HTTPException
import libs.lb_system as lb_system
from libs.lb_database import get_reservations_with_incomplete_weighings

class GenericRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/list/serial-ports', self.getSerialPorts)
        self.router.add_api_route('/list/reservations-open', self.getReservationsOpen, methods=['GET'])

    async def getSerialPorts(self):
        """Restituisce una lista delle porte seriali disponibili."""
        try:
            status, data = lb_system.list_serial_port()
            if status:
                return {"list_serial_ports": data}
            else:
                raise HTTPException(status_code=400, detail="Unable to retrieve serial ports")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        
    async def getReservationsOpen(self):
        return get_reservations_with_incomplete_weighings()