from fastapi import APIRouter, Depends
import libs.lb_config as lb_config
import modules.md_weigher.md_weigher as md_weigher
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType, Data
from applications.router.weigher.config_weigher import ConfigWeigher
import asyncio

class DataInExecutionRouter(ConfigWeigher):
    def __init__(self):
        super().__init__()
        
        self.router_data_in_execution = APIRouter()
    
        self.router_data_in_execution.add_api_route('/data_in_execution', self.GetDataInExecution, methods=['GET'])
        self.router_data_in_execution.add_api_route('/data_in_execution', self.SetDataInExecution, methods=['PATCH'])
        self.router_data_in_execution.add_api_route('/data_in_execution', self.DeleteDataInExecution, methods=['DELETE'])
    
    async def GetDataInExecution(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        return self.weighers_data[instance.instance_name][instance.weigher_name]["data"]

    async def SetDataInExecution(self, data_dto: DataDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        self.weighers_data[instance.instance_name][instance.weigher_name]["data"].data_in_execution.setAttribute(data_dto.data_in_execution)
        if data_dto.id_selected is not None:
            try:
                self.weighers_data[instance.instance_name][instance.weigher_name]["data"].id_selected.setAttribute(data_dto.id_selected.id)
            except Exception as e:
                return e
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"] = self.weighers_data[instance.instance_name][instance.weigher_name]["data"].dict()
        lb_config.saveconfig()
        await self.BroadcastDataChanged(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
        return self.weighers_data[instance.instance_name][instance.weigher_name]["data"].dict()

    async def DeleteDataInExecution(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        self.weighers_data[instance.instance_name][instance.weigher_name]["data"].data_in_execution.deleteAttribute()
        self.weighers_data[instance.instance_name][instance.weigher_name]["data"].id_selected.deleteAttribute()
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"] = self.weighers_data[instance.instance_name][instance.weigher_name]["data"].dict()
        lb_config.saveconfig()
        await self.BroadcastDataChanged(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
        return self.weighers_data[instance.instance_name][instance.weigher_name]["data"].dict()
                        
    async def BroadcastDataChanged(self, instance_name, weigher_name):
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.weighers_data[instance_name][weigher_name]["data"].dict()))
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.weighers_data[instance_name][weigher_name]["data"].dict()))