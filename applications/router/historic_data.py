from fastapi import APIRouter, HTTPException
from libs.lb_database import filter_data

class HistoricDataRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('/weighings/in', self.getWeighingsIn, methods=['GET'])

    async def getWeighingsIn(self):
        return filter_data("weighing", { "pid2": None })