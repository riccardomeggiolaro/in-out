from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from modules.md_database.md_database import SessionLocal, CameraPlateHistory
from sqlalchemy import func, desc
from applications.router.anagrafic.web_sockets import WebSocket

class AddCameraPlateDTO(BaseModel):
    camera_id: str
    plate: str

class CameraPlateHistoryRouter(WebSocket):
    def __init__(self):
        super().__init__()

        self.router = APIRouter()

        self.router.add_api_route('/add', self.addCameraPlate, methods=['POST'])
        self.router.add_api_route('/list', self.getLatestPlates, methods=['GET'])
        self.router.add_api_route('/list/{camera_id}', self.getLatestPlatesByCamera, methods=['GET'])

    async def addCameraPlate(self, data: AddCameraPlateDTO):
        """
        Endpoint per aggiungere una nuova targa rilevata da una telecamera.
        Mantiene automaticamente solo le ultime 5 targhe per telecamera.
        """
        try:
            # Filtra targhe troppo corte (meno di 5 caratteri)
            if len(data.plate) < 5:
                return {
                    "success": False,
                    "message": "Plate too short (minimum 5 characters)",
                    "plate": data.plate
                }

            db_session = SessionLocal()

            # Aggiungi la nuova targa
            new_plate = CameraPlateHistory(
                camera_id=data.camera_id,
                plate=data.plate.upper(),
                timestamp=datetime.now()
            )
            db_session.add(new_plate)
            db_session.commit()

            # Conta quante targhe ci sono per questa telecamera
            plates_count = db_session.query(CameraPlateHistory).filter(
                CameraPlateHistory.camera_id == data.camera_id
            ).count()

            # Se ci sono più di 5 targhe, elimina quelle più vecchie
            if plates_count > 5:
                # Trova l'ID della quinta targa più recente
                fifth_plate = db_session.query(CameraPlateHistory.id).filter(
                    CameraPlateHistory.camera_id == data.camera_id
                ).order_by(desc(CameraPlateHistory.timestamp)).offset(4).limit(1).scalar()

                # Elimina tutte le targhe più vecchie della quinta
                if fifth_plate:
                    db_session.query(CameraPlateHistory).filter(
                        CameraPlateHistory.camera_id == data.camera_id,
                        CameraPlateHistory.id < fifth_plate
                    ).delete()
                    db_session.commit()

            # Recupera le ultime 5 targhe per questa telecamera
            latest_plates = db_session.query(CameraPlateHistory).filter(
                CameraPlateHistory.camera_id == data.camera_id
            ).order_by(desc(CameraPlateHistory.timestamp)).limit(5).all()

            plates_data = [{
                "id": plate.id,
                "camera_id": plate.camera_id,
                "plate": plate.plate,
                "timestamp": plate.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for plate in latest_plates]

            db_session.close()

            # Broadcast WebSocket update
            await self.broadcastAddAnagrafic("camera_plate_history", {
                "camera_id": data.camera_id,
                "plates": plates_data
            })

            return {
                "success": True,
                "message": "Plate added successfully",
                "camera_id": data.camera_id,
                "plate": data.plate,
                "plates": plates_data
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def getLatestPlates(self):
        """
        Endpoint per recuperare le ultime 5 targhe per ogni telecamera.
        Ritorna un dizionario con camera_id come chiave.
        """
        try:
            db_session = SessionLocal()

            # Trova tutte le telecamere distinte
            cameras = db_session.query(CameraPlateHistory.camera_id).distinct().all()

            result = {}

            for (camera_id,) in cameras:
                # Recupera le ultime 5 targhe per questa telecamera
                plates = db_session.query(CameraPlateHistory).filter(
                    CameraPlateHistory.camera_id == camera_id
                ).order_by(desc(CameraPlateHistory.timestamp)).limit(5).all()

                result[camera_id] = [{
                    "id": plate.id,
                    "plate": plate.plate,
                    "timestamp": plate.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                } for plate in plates]

            db_session.close()

            return {
                "success": True,
                "data": result
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def getLatestPlatesByCamera(self, camera_id: str):
        """
        Endpoint per recuperare le ultime 5 targhe per una specifica telecamera.
        """
        try:
            db_session = SessionLocal()

            # Recupera le ultime 5 targhe per questa telecamera
            plates = db_session.query(CameraPlateHistory).filter(
                CameraPlateHistory.camera_id == camera_id
            ).order_by(desc(CameraPlateHistory.timestamp)).limit(5).all()

            plates_data = [{
                "id": plate.id,
                "plate": plate.plate,
                "timestamp": plate.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for plate in plates]

            db_session.close()

            return {
                "success": True,
                "camera_id": camera_id,
                "plates": plates_data
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
