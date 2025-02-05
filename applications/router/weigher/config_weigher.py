from fastapi import APIRouter, Depends, HTTPException
from applications.router.weigher.callback_weigher import CallbackWeigher
import libs.lb_config as lb_config
from applications.utils.utils_weigher import InstanceNameDTO, InstanceNameWeigherDTO, get_query_params_name, get_query_params_name_node
from applications.utils.utils import validate_time
import modules.md_weigher.md_weigher as md_weigher
from modules.md_weigher.dto import ConfigurationDTO, SetupWeigherDTO, ChangeSetupWeigherDTO
from typing import Union
from libs.lb_system import SerialPort, Tcp
from applications.router.weigher.types import Data

class ConfigWeigher(CallbackWeigher):
    def __init__(self):
        super().__init__()
        
        self.router_config_weigher = APIRouter()
    
        self.router_config_weigher.add_api_route('/all/instance', self.GetAllInstance, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance', self.GetInstance, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance', self.AddInstance, methods=['POST'])
        self.router_config_weigher.add_api_route('/instance', self.DeleteInstance, methods=['DELETE'])
        self.router_config_weigher.add_api_route('/instance/node', self.GetInstanceWeigher, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance/node', self.AddInstanceWeigher, methods=['POST'])
        self.router_config_weigher.add_api_route('/instance/node', self.SetInstanceWeigher, methods=['PATCH'])
        self.router_config_weigher.add_api_route('/instance/node', self.DeleteInstanceWeigher, methods=['DELETE'])
        self.router_config_weigher.add_api_route('/instance/connection', self.SetInstanceConnection, methods=['PATCH'])
        self.router_config_weigher.add_api_route('/instance/connection', self.DeleteInstanceConnection, methods=['DELETE'])
        self.router_config_weigher.add_api_route('/instance/time_between_actions/{time}', self.SetInstanceTimeBetweenActions, methods=['PATCH'])

    async def GetAllInstance(self):
        return md_weigher.module_weigher.getAllInstance()

    async def GetInstance(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        return md_weigher.module_weigher.getInstance(instance_name=instance.instance_name)

    async def AddInstance(self, configuration: ConfigurationDTO):
        response = md_weigher.module_weigher.createInstance(configuration=configuration)
        self.addInstanceSocket(configuration.name)
        instance_to_save = response.copy()
        del instance_to_save[configuration.name]["connection"]["connected"]
        lb_config.g_config["app_api"]["weighers"] = instance_to_save
        lb_config.saveconfig()
        return response

    async def DeleteInstance(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        response = md_weigher.module_weigher.deleteInstance(instance_name=instance.instance_name)
        self.deleteInstanceSocket(instance_name=instance.instance_name)
        lb_config.g_config["app_api"]["weighers"].pop(instance.instance_name)
        lb_config.saveconfig()
        return { "deleted": response }

    async def GetInstanceWeigher(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        return md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

    async def AddInstanceWeigher(self, setup: SetupWeigherDTO, instance: InstanceNameDTO = Depends(get_query_params_name)):
        response = md_weigher.module_weigher.addInstanceWeigher(
            instance_name=instance.instance_name,
            setup=setup,
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic,
            cb_weighing=self.Callback_Weighing,
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_action_in_execution=self.Callback_ActionInExecution,
            cb_rele=self.Callback_Rele
        )
        data = Data(**{})
        self.addInstanceWeigherSocket(instance_name=instance.instance_name, weigher_name=setup.name, data=data)
        weigher_created = response.copy()
        del weigher_created[setup.name]["terminal_data"]
        del weigher_created[setup.name]["status"]
        weigher_created[setup.name]["data"] = Data(**{}).dict()
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][setup.name] = weigher_created[setup.name]
        lb_config.saveconfig()
        return response

    async def SetInstanceWeigher(self, setup: ChangeSetupWeigherDTO = {}, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        response = md_weigher.module_weigher.setInstanceWeigher(
            instance_name=instance.instance_name,
            weigher_name=instance.weigher_name, 
            setup=setup,
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic,
            cb_weighing=self.Callback_Weighing,
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_action_in_execution=self.Callback_ActionInExecution,
            cb_rele=self.Callback_Rele
        )
        weigher_name = instance.weigher_name
        if setup.name != "undefined":
            data = Data(**lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"])
            self.deleteInstanceWeigherSocket(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
            self.addInstanceWeigherSocket(instance_name=instance.instance_name, weigher_name=setup.name, data=data)
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][setup.name] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"].pop(instance.weigher_name)
            response[setup.name] = response.pop(instance.weigher_name)
            weigher_name = setup.name
        weigher_set = response.copy()
        del weigher_set[weigher_name]["terminal_data"]
        del weigher_set[weigher_name]["status"]
        for key, value in weigher_set[weigher_name].items():
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name][key] = value
        lb_config.saveconfig()
        return response

    async def DeleteInstanceWeigher(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        response = md_weigher.module_weigher.deleteInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
        self.deleteDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
        self.deleteIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
        self.deleteInstanceWeigherSocket(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
        del lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]
        lb_config.saveconfig()
        return { "deleted": response }

    async def SetInstanceConnection(self, connection: Union[SerialPort, Tcp], instance: InstanceNameDTO = Depends(get_query_params_name)):
        response = md_weigher.module_weigher.setInstanceConnection(instance_name=instance.instance_name, conn=connection)
        conn_to_save = response.copy()
        del conn_to_save["connected"]
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["connection"] = conn_to_save
        lb_config.saveconfig()
        return response

    async def DeleteInstanceConnection(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        response = md_weigher.module_weigher.getInstanceConnection(instance_name=instance.instance_name)
        del response["connected"]
        if not response:
            response = False
        else:
            response = md_weigher.module_weigher.deleteInstanceConnection(instance_name=instance.instance_name)
            del response["connected"]
            conn_to_save = response.copy()
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["connection"] = conn_to_save
            lb_config.saveconfig()
            response = True
        return { "deleted": response }

    async def SetInstanceTimeBetweenActions(self, time: Union[int, float] = Depends(validate_time), instance: InstanceNameDTO = Depends(get_query_params_name)):
        new_time_set = md_weigher.module_weigher.setInstanceTimeBetweenActions(instance_name=instance.instance_name, time_between_actions=time)
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["time_between_actions"] = time
        lb_config.saveconfig()
        return { "time_between_actions": new_time_set }