from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response
from typing import Dict, Union, Optional
from modules.md_database.md_database import upload_file_datas_required_columns
from modules.md_database.dtos.reservation import Reservation
from modules.md_database.functions.filter_data import filter_data
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.delete_all_data import delete_all_data
from modules.md_database.functions.load_datas_into_db import load_datas_into_db
from modules.md_database.functions.get_list_reservations import get_list_reservations
import pandas as pd
import numpy as np
from applications.utils.utils import get_query_params
from applications.router.anagrafic.web_sockets import WebSocket

class ReservationRouter(WebSocket):
    def __init__(self):
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListReservations, methods=['GET'])
        self.router.add_api_route('/list/uncomplete', self.getListReservationWithUncompleteWeighings, methods=['GET'])
        # self.router.add_api_route('', self.addSubject, methods=['POST'])
        # self.router.add_api_route('/{id}', self.setSubject, methods=['PATCH'])
        self.router.add_api_route('/{id}', self.deleteReservation, methods=['DELETE'])
        self.router.add_api_route('', self.deleteAllReservations, methods=['DELETE'])

    async def getListReservations(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None):
        try:
            if limit is not None:
                del query_params["limit"]
            if offset is not None:
                del query_params["offset"]
            data, total_rows = get_list_reservations(True, query_params, limit, offset, ('date_created', 'desc'))
            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def getListReservationWithUncompleteWeighings(self, query_params: Dict[str, int] = Depends(get_query_params)):
        return get_list_reservations(True)

    # async def addSubject(self, body: AddSubjectDTO):
    #     try:
    #         add_data("subject", body.dict())
    #         return {"message": "Data added successfully"}
    #     except Exception as e:
    #         raise HTTPException(status_code=400, detail=f"{e}")

    # async def setSubject(self, id: int, body: SetSubjectDTO):
    #     try:
    #         update_data("subject", id, body.dict())
    #     except Exception as e:
    #         raise HTTPException(status_code=404, detail=f"{e}")

    #     return {"message": "Data updated successfully"}

    async def deleteReservation(self, id: int):
        try:
            data = delete_data("reservation", id)
            await self.broadcastDeleteAnagrafic("reservation", Reservation(**data).dict())
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def deleteAllReservations(self):
        try:
            deleted_count = delete_all_data("reservation")
            await self.broadcastDeleteAnagrafic("reservation", None)
            return {
                "deleted_count": deleted_count,
            }
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)