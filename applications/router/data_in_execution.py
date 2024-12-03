from fastapi import APIRouter, Depends
import libs.lb_config as lb_config
import modules.md_weigher.md_weigher as md_weigher
from applications.utils.instance_weigher import InstanceNameNodeDTO
from applications.utils.utils import get_query_params_name_node
from modules.md_weigher.dto import DataDTO
from modules.md_weigher.types import DataInExecution as DataInExecutionType

class DataInExecutionRouter:
    def __init__(self):
        self.router = APIRouter()
    
        self.router.add_api_route('/data_in_execution', self.GetDataInExecution, methods=['GET'])
        self.router.add_api_route('/data_in_execution', self.SetDataInExecution, methods=['PATCH'])
        self.router.add_api_route('/data_in_execution', self.DeleteDataInExecution, methods=['DELETE'])
    
    async def GetDataInExecution(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        status, data = md_weigher.module_weigher.instances[instance.name].getData(node=instance.node)
        return {
            "instance": instance,
            "data": data,
            "status": status
        }

    async def SetDataInExecution(self, data_dto: DataDTO, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        data_in_execution = DataInExecutionType(**data_dto.data_in_execution.dict())
        status, data = md_weigher.module_weigher.instances[instance.name].setDataInExecution(node=instance.node, data_in_execution=data_in_execution, call_callback=True)
        if data_dto.id_selected is not None:
            status, data = md_weigher.module_weigher.instances[instance.name].setIdSelected(node=instance.node, new_id=data_dto.id_selected.id, call_callback=True)
        node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
        index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
        lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data"] = data
        lb_config.saveconfig()
        return {
            "instance": instance,
            "data": data,
            "status": status
        }

    async def DeleteDataInExecution(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        status, data = md_weigher.module_weigher.instances[instance.name].deleteDataInExecution(node=instance.node, call_callback=True)
        node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
        index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
        lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data"]["data_in_execution"] = data
        lb_config.saveconfig()
        return {
            "instance": instance,
            "data": data,
            "status": status
        }