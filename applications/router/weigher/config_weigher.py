from fastapi import APIRouter, Depends, HTTPException
from applications.router.weigher.callback_weigher import CallbackWeigher
import libs.lb_config as lb_config
from applications.utils.instance_weigher import InstanceNameDTO, InstanceNameNodeDTO
from applications.utils.utils import get_query_params_name, get_query_params_name_node
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
        self.router_config_weigher.add_api_route('/instance', self.CreateInstance, methods=['POST'])
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

    async def CreateInstance(self, configuration: ConfigurationDTO):
        if configuration.name in md_weigher.module_weigher.getAllInstance():
            return HTTPException(status_code=400, detail="Name just exist")
        return md_weigher.module_weigher.createInstance(configuration=configuration)

    async def DeleteInstance(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        md_weigher.module_weigher.deleteInstance(instance.name)

    async def GetInstanceNode(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        response = md_weigher.module_weigher.getInstanceNode(name=instance.name, node=instance.node)
        if not response:
            raise HTTPException(status_code=404, detail='Not found')
        return response

    async def AddInstanceNode(self, node: SetupWeigherDTO, instance: InstanceNameDTO = Depends(get_query_params_name)):
        if any(node.node == current_node["node"] for current_node in md_weigher.module_weigher.getAllInstanceNode(name=instance.name)):
            raise HTTPException(status_code=400, detail='Node just exist')
        return md_weigher.module_weigher.addInstanceNode(
            name=instance.name, 
            node=node,
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic,
            cb_weighing=self.Callback_Weighing,
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_data=self.Callback_Data,
            cb_action_in_execution=self.Callback_ActionInExecution
        )

    async def SetInstanceNode(self, setup: ChangeSetupWeigherDTO = {}, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        if any(setup.node == current_node["node"] for current_node in md_weigher.module_weigher.getAllInstanceNode(name=instance.name)):
            raise HTTPException(status_code=400, detail='Node just exist')
        response = md_weigher.module_weigher.setInstanceNode(
            name=instance.name,
            node=instance.node, 
            node_changed=setup,
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic,
            cb_weighing=self.Callback_Weighing,
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_data=self.Callback_Data,
            cb_action_in_execution=self.Callback_ActionInExecution
        )
        if response:
            return response
        else:
            raise HTTPException(status_code=404, detail='Not found')

    async def DeleteInstanceNode(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
        node_removed = md_weigher.module_weigher.instances[instance.name].deleteNode(instance.node)
        if node_removed:
            return {
                "removed": node_removed
            }
        else:
            raise HTTPException(status_code=404, detail='Not found')

    async def SetInstanceConnection(self, connection: Union[SerialPort, Tcp], instance: InstanceNameDTO = Depends(get_query_params_name)):
        return md_weigher.module_weigher.setInstanceConnection(name=instance.name, conn=connection)

    async def DeleteInstanceConnection(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        return md_weigher.module_weigher.deleteInstanceConnection(name=instance.name)

    async def SetInstanceTimeBetweenActions(self, time: Union[int, float], instance: InstanceNameDTO = Depends(get_query_params_name)):
        if time <= 0:
            return {
                "message": "Time must be greater than 0"
            }
        result = md_weigher.module_weigher.instances[instance.name].setTimeBetweenActions(time=time)
        connection = md_weigher.module_weigher.instances[instance.name].getConnection()
        lb_config.g_config["app_api"]["weighers"][instance.name]["time_between_actions"] = result
        lb_config.saveconfig()
        return {
            "instance": instance,
            "connection": connection,
            "time_between_actions": result
        }

        async def deleteInstanceWeigher(self, name):
            deleted = False
        
            if name in self.weighers_sockets:
                for node in self.weighers_sockets[name]:
                    await self.weighers_sockets[name][node].manager_realtime.broadcast("Weigher instance deleted")
                    self.weighers_sockets[name][node].manager_realtime.disconnect_all()
                    await self.weighers_sockets[name][node].manager_diagnostic.broadcast("Weigher instance deleted")
                    self.weighers_sockets[name][node].manager_diagnostic.disconnect_all()
                    await self.weighers_sockets[name][node].manager_execution.broadcast("Weigher instance deleted")
                    self.weighers_sockets[name][node].manager_execution.disconnect_all()
                self.weighers_sockets[name].stop()
                deleted = True
            return deleted