from fastapi import APIRouter, HTTPException
from libs.lb_database import filter_data

router = APIRouter()

@router.get("/weighings/in")
async def getWeighings():
    try:
        data = filter_data("weighing", { "pid2": None })
        return data
    except Exception as e:
        return HTTPException(status_code=400, detail=f"{e}")