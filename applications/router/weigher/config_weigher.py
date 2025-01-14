from fastapi import APIRouter, Depends, HTTPException
from applications.router.weigher.callback_weigher import CallbackWeigher
import libs.lb_config as lb_config
from applications.utils.utils_weigher import InstanceNameDTO, InstanceNameNodeDTO, get_query_params_name, get_query_params_name_node
from applications.utils.utils import validate_time
import modules.md_weigher.md_weigher as md_weigher
from modules.md_weigher.dto import ConfigurationDTO, SetupWeigherDTO, ChangeSetupWeigherDTO
from typing import Union
from libs.lb_system import SerialPort, Tcp

class ConfigWeigher(CallbackWeigher):
    def __init__(self):
        super().__init__()
        
        self.router_config_weigher = APIRouter()
    
        self.router_config_weigher.add_api_route('/all/instance', self.GetAllInstance, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance', self.GetInstance, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance', self.AddInstance, methods=['POST'])
        self.router_config_weigher.add_api_route('/instance', self.DeleteInstance, methods=['DELETE'])
        self.router_config_weigher.add_api_route('/instance/node', self.GetInstanceNode, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance/node', self.AddInstanceNode, methods=['POST'])
        self.router_config_weigher.add_api_route('/instance/node', self.SetInstanceNode, methods=['PATCH'])
        self.router_config_weigher.add_api_route('/instance/node', self.DeleteInstanceNode, methods=['DELETE'])
        self.router_config_weigher.add_api_route('/instance/connection', self.SetInstanceConnection, methods=['PATCH'])
        self.router_config_weigher.add_api_route('/instance/connection', self.DeleteInstanceConnection, methods=['DELETE'])
        self.router_config_weigher.add_api_route('/instance/time_between_actions/{time}', self.SetInstanceTimeBetweenActions, methods=['PATCH'])

    async def GetAllInstance(self):
        return md_weigher.module_weigher.getAllInstance()

    async def GetInstance(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        return md_weigher.module_weigher.getInstance(instance.name)

    async def AddInstance(self, configuration: ConfigurationDTO):
        response = md_weigher.module_weigher.createInstance(configuration=configuration)
        self.addInstanceSocket(configuration.name)
        return response

    async def DeleteInstance(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        md_weigher.module_weigher.deleteInstance(instance.name)
        self.deleteInstanceSocket(instance.name)
        return { "deleted": True }

    async def GetInstanceNode(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        return md_weigher.module_weigher.getInstanceNode(name=instance.name, node=instance.node)

    async def AddInstanceNode(self, setup: SetupWeigherDTO, instance: InstanceNameDTO = Depends(get_query_params_name)):
        response = md_weigher.module_weigher.addInstanceNode(
            name=instance.name,
            setup=setup,
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic,
            cb_weighing=self.Callback_Weighing,
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_data_in_execution=self.Callback_DataInExecution,
            cb_action_in_execution=self.Callback_ActionInExecution
        )
        self.addInstanceNodeSocket(instance.name, setup.node)
        return response

    async def SetInstanceNode(self, setup: ChangeSetupWeigherDTO = {}, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        response = md_weigher.module_weigher.setInstanceNode(
            name=instance.name,
            node=instance.node, 
            setup=setup,
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic,
            cb_weighing=self.Callback_Weighing,
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_data_in_execution=self.Callback_DataInExecution,
            cb_action_in_execution=self.Callback_ActionInExecution
        )
        if setup.node != "undefined":
            self.deleteInstanceNodeSocket(instance.name, instance.node)
            self.addInstanceNodeSocket(instance.name, setup.node)
        return response

    async def DeleteInstanceNode(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        md_weigher.module_weigher.deleteInstanceNode(name=instance.name, node=instance.node)
        self.deleteInstanceNodeSocket(instance.name, instance.node)
        return { "deleted": True }

    async def SetInstanceConnection(self, connection: Union[SerialPort, Tcp], instance: InstanceNameDTO = Depends(get_query_params_name)):
        return md_weigher.module_weigher.setInstanceConnection(name=instance.name, conn=connection)

    async def DeleteInstanceConnection(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        connection = md_weigher.module_weigher.getInstanceConnection(name=instance.name, delete_connected=True)
        if not connection:
            return { "deleted": False }
        md_weigher.module_weigher.deleteInstanceConnection(name=instance.name)
        return { "deleted": True }

    async def SetInstanceTimeBetweenActions(self, time: Union[int, float] = Depends(validate_time), instance: InstanceNameDTO = Depends(get_query_params_name)):
        new_time_set = md_weigher.module_weigher.setInstanceTimeBetweenActions(name=instance.name, time_between_actions=time)
        return { "time_between_actions": new_time_set }