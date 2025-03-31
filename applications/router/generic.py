from fastapi import APIRouter, HTTPException
import libs.lb_system as lb_system

class GenericRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/list/serial-ports', self.getSerialPorts)

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