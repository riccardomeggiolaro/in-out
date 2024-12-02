from fastapi import APIRouter, HTTPException
from libs.lb_database import filter_data

class HistoricData:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('/weighings/in', self.getWeighingsIn, methods=['GET'])

    async def getWeighingsIn(self):
        try:
            data = filter_data("weighing", { "pid2": None })
            return data
        except Exception as e:
            return HTTPException(status_code=400, detail=f"{e}")