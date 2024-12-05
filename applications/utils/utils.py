from fastapi import Request, Depends, HTTPException
from typing import Dict, Union
import modules.md_weigher.md_weigher as md_weigher
import libs.lb_log as lb_log

async def get_query_params(request: Request) -> Dict[str, Union[str, int]]:
	"""
	Converts URL query parameters into a dictionary
	"""
	return dict(request.query_params)

# Funzione di validazione per time
async def validate_time(time: Union[int, float]) -> Union[int, float]:
    if time <= 0:
        raise HTTPException(status_code=400, detail="Time must be greater than 0")
    return time