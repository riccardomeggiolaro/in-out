from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Union, Optional
from applications.utils.utils import get_query_params
from modules.md_database.functions.get_list_in_out import get_list_in_out
from datetime import datetime

class OpenToCustomerRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/in-out/list', self.getListInOut, methods=['GET'])

    async def getListInOut(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, onlyInOutWithWeight2: bool = False):
        try:
            # Handle limit and offset
            if "limit" in query_params:
                del query_params["limit"]
            if "offset" in query_params:
                del query_params["offset"]
                
            # Handle date query_params for weights
            if fromDate is not None:
                del query_params["fromDate"]
                
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del query_params["toDate"]

            if "onlyInOutWithoutWeight2" in query_params:
                del query_params["onlyInOutWithoutWeight2"]
                
            # Call get_list_in_out with prepared query_params
            data, total_rows = get_list_in_out(
                filters=query_params,
                not_closed=False,
                only_in_out_with_weight2=onlyInOutWithWeight2,
                only_in_out_without_weight2=False,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('id', 'desc'),
                excludeTestWeighing=True,
                get_is_last=False
            )
            
            return {
                "data": data,
                "total_rows": total_rows,
                "buffer": self.buffer
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")