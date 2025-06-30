from fastapi import APIRouter, HTTPException
import libs.lb_system as lb_system
from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from applications.utils.utils_auth import create_access_token

class GenericRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/list/serial-ports', self.getSerialPorts)
        self.router.add_api_route('/create/cam-capture-plate-access-token', self.createCamCapturePlateAccessToken)

    async def getSerialPorts(self):
        """Restituisce una lista delle porte seriali disponibili e il tempo impiegato per ottenerla."""
        import time
        start_time = time.time()
        try:
            status, data = lb_system.list_serial_port()
            elapsed = time.time() - start_time
            if status:
                return {"list_serial_ports": data, "elapsed_seconds": elapsed}
            else:
                raise HTTPException(status_code=400, detail="Unable to retrieve serial ports")
        except Exception as e:
            elapsed = time.time() - start_time
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)} (elapsed: {elapsed:.3f}s)")
        
    async def createCamCapturePlateAccessToken(self):
        try:
            cam_capture_plate = get_data_by_attribute("user", "username", "camcaptureplate")
            cam_capture_plate["date_created"] = cam_capture_plate["date_created"].isoformat()
            if cam_capture_plate:
                return {
                    "access_token": create_access_token(cam_capture_plate)
                }
            # Se la password è errata, restituisci un errore generico
            raise HTTPException(status_code=404, detail="L'utente delle telecamere per l'acquisizione delle targhe non esiste")
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            # Gestisce eventuali errori imprevisti (come la mancanza dell'utente)
            raise HTTPException(
                status_code=status_code,
                detail=detail
            )