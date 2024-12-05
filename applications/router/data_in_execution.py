from fastapi import APIRouter, Depends
import libs.lb_config as lb_config
import modules.md_weigher.md_weigher as md_weigher
from applications.utils.utils_weigher import InstanceNameNodeDTO, get_query_params_name_node
from modules.md_weigher.dto import DataDTO
from modules.md_weigher.types import DataInExecution as DataInExecutionType

class DataInExecutionRouter:
    def __init__(self):
        self.router = APIRouter()
    
        self.router.add_api_route('/data_in_execution', self.GetDataInExecution, methods=['GET'])
        self.router.add_api_route('/data_in_execution', self.SetDataInExecution, methods=['PATCH'])
        self.router.add_api_route('/data_in_execution', self.DeleteDataInExecution, methods=['DELETE'])
    
    async def GetDataInExecution(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        status, data = md_weigher.module_weigher.getData(name=instance.name, node=instance.node)
        return {
            "instance": instance,
            "data": data,
            "status": status
        }

    async def SetDataInExecution(self, data_dto: DataDTO, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        status, data = md_weigher.module_weigher.setData(name=instance.name, node=instance.node, data_dto=data_dto, call_callback=True)
        return {
            "instance": instance,
            "data": data,
            "status": status
        }

    async def DeleteDataInExecution(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        status, data = md_weigher.module_weigher.deleteData(name=instance.name, node=instance.node, call_callback=True)
        return {
            "instance": instance,
            "data": data,
            "status": status
        }