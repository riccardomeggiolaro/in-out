from fastapi import APIRouter, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.routing import Mount
from applications.router.weigher.command_weigher import CommandWeigherRouter
import libs.lb_config as lb_config
from applications.utils.utils_weigher import InstanceNameDTO, InstanceNameWeigherDTO, get_query_params_name, get_query_params_name_node
from applications.utils.utils import validate_time
import modules.md_weigher.md_weigher as md_weigher
from modules.md_weigher.dto import ConfigurationDTO, SetupWeigherDTO, ChangeSetupWeigherDTO
from typing import Union
from libs.lb_system import SerialPort, Tcp
from applications.router.weigher.types import Data
from applications.middleware.super_admin import is_super_admin
from applications.router.weigher.dto import PathDTO
from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from applications.utils.utils_auth import create_access_token
import socket

class ConfigWeigher(CommandWeigherRouter):
    def __init__(self):
        super().__init__()
        
        self.router_config_weigher = APIRouter()
    
        self.router_config_weigher.add_api_route('/configuration', self.GetAllConfiguration, methods=['GET'])
        self.router_config_weigher.add_api_route('/configuration/use-reservation/{use_reservation}', self.SetUseReservation, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/configuration/use-white-list/{use_white_list}', self.SetUseWhiteList, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/configuration/use-badge/{use_badge}', self.SetUseTag, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/configuration/return-pdf-copy-after-weighing/{return_pdf_copy_after_weighing}', self.SetReturnCopyPdfWeighing, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/configuration/path-pdf', self.SavePathPdf, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/configuration/path-csv', self.SavePathCsv, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/configuration/path-img', self.SavePathImg, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/all/instance', self.GetAllInstance, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance', self.GetInstance, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance', self.AddInstance, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/instance', self.DeleteInstance, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/instance/node', self.GetInstanceWeigher, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance/node', self.AddInstanceWeigher, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/instance/node', self.SetInstanceWeigher, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/instance/node', self.DeleteInstanceWeigher, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/instance/node/endpoint', self.GetInstanceWeigherEndpoint, methods=['GET'])
        self.router_config_weigher.add_api_route('/instance/connection', self.SetInstanceConnection, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/instance/connection', self.DeleteInstanceConnection, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router_config_weigher.add_api_route('/instance/time-between-actions/{time}', self.SetInstanceTimeBetweenActions, methods=['PATCH'], dependencies=[Depends(is_super_admin)])

    async def GetAllConfiguration(self):
        return lb_config.g_config["app_api"]

    async def SetReturnCopyPdfWeighing(self, return_pdf_copy_after_weighing: bool):
        lb_config.g_config["app_api"]["return_pdf_copy_after_weighing"] = return_pdf_copy_after_weighing
        lb_config.saveconfig()
        return { "return_pdf_copy_after_weighing": return_pdf_copy_after_weighing }

    async def SetUseReservation(self, use_reservation: bool):
        lb_config.g_config["app_api"]["use_reservation"] = use_reservation
        lb_config.saveconfig()
        return { "use_reservation": use_reservation }

    async def SetUseWhiteList(self, use_white_list: bool):
        lb_config.g_config["app_api"]["use_white_list"] = use_white_list
        lb_config.saveconfig()
        return { "use_white_list": use_white_list }

    async def SetUseTag(self, use_badge: bool):
        lb_config.g_config["app_api"]["use_badge"] = use_badge
        lb_config.saveconfig()
        return { "use_badge": use_badge }

    async def SavePathPdf(self, body: PathDTO):
        path = body.path
        lb_config.g_config["app_api"]["path_pdf"] = path
        lb_config.saveconfig()
        return { "path_pdf": path }

    async def SavePathCsv(self, body: PathDTO):
        path = body.path
        lb_config.g_config["app_api"]["path_csv"] = path
        lb_config.saveconfig()
        return { "path_csv": path }

    async def SavePathImg(self, body: PathDTO):
        from applications.app_api import app
        path = body.path if body.path else ''
        lb_config.g_config["app_api"]["path_img"] = path
        lb_config.saveconfig()
        for route in app.routes:
            if route.path == "/images":
                list_path_images = []
                if path:
                    list_path_images.append(path)
                route._base_app.directory = path
                route._base_app.all_directories = list_path_images
                route.app.directory = path
                route.app.all_directories = list_path_images
        return { "path_img": path }

    async def GetAllInstance(self):
        return lb_config.g_config["app_api"]["weighers"]

    async def GetInstance(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        return md_weigher.module_weigher.getInstance(instance_name=instance.instance_name)

    async def AddInstance(self, configuration: ConfigurationDTO):
        response = md_weigher.module_weigher.createInstance(configuration=configuration)
        self.addInstanceSocket(configuration.name)
        instance_to_save = response.copy()
        del instance_to_save[configuration.name]["connection"]["connected"]
        lb_config.g_config["app_api"]["weighers"][configuration.name] = instance_to_save[configuration.name]
        lb_config.saveconfig()
        return response

    async def DeleteInstance(self, instance: InstanceNameDTO = Depends(get_query_params_name)):
        response = md_weigher.module_weigher.deleteInstance(instance_name=instance.instance_name)
        self.deleteInstanceSocket(instance_name=instance.instance_name)
        lb_config.g_config["app_api"]["weighers"].pop(instance.instance_name)
        lb_config.saveconfig()
        return { "deleted": response }

    async def GetInstanceWeigher(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        instance_weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
        instance_weigher[instance.instance_name]["max_theshold"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["max_theshold"]
        instance_weigher[instance.instance_name]["events"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]
        instance_weigher[instance.instance_name]["rele"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["rele"]
        instance_weigher[instance.instance_name]["printer_name"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["printer_name"]
        return instance_weigher

    async def AddInstanceWeigher(self, setup: SetupWeigherDTO, instance: InstanceNameDTO = Depends(get_query_params_name)):
        nodes = []
        for instance_name in lb_config.g_config["app_api"]["weighers"]:
            for node in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"]:
                nodes.append(node)
        if setup.name in nodes:
            details = [{"type": "value_error", "loc": ["", "name"], "msg": "Nome già esistente", "input": setup.name, "ctx": {"error":{}}}]
            raise HTTPException(status_code=400, detail=details)
        response = md_weigher.module_weigher.addInstanceWeigher(
            instance_name=instance.instance_name,
            setup=setup,
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic,
            cb_weighing=self.Callback_Weighing,
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_action_in_execution=self.Callback_ActionInExecution,
            cb_rele=self.Callback_Rele,
            cb_code_identify=self.Callback_WeighingByIdentify
        )
        data = Data(**{})
        self.addInstanceWeigherSocket(instance_name=instance.instance_name, weigher_name=setup.name, data=data)
        weigher_created = response.copy()
        del weigher_created[setup.name]["terminal_data"]
        del weigher_created[setup.name]["status"]
        weigher_created[setup.name]["printer_name"] = setup.printer_name
        weigher_created[setup.name]["number_of_prints"] = setup.number_of_prints
        weigher_created[setup.name]["data"] = Data(**{}).dict()
        weigher_created[setup.name]["max_theshold"] = setup.max_theshold
        weigher_created[setup.name]["events"] = {
            "realtime": {
                "over_min": {
                    "set_rele": [rele.dict() for rele in setup.over_min]
                },
                "under_min": {
                    "set_rele": [rele.dict() for rele in setup.under_min]
                }
            },
            "weighing": {
                "report": {
                    "in": setup.report_on_in if setup.report_on_in is not None else False,
                    "out": setup.report_on_out if setup.report_on_out is not None else False
                },
                "set_rele": [rele.dict() for rele in setup.weighing],
                "cams": [{"picture": str(cam.picture), "live": str(cam.live), "active": cam.active} for cam in setup.cams]
            }
        }
        weigher_created[setup.name]["rele"] = {}
        reles = setup.over_min + setup.under_min + setup.weighing
        for obj in reles:
            rele = obj.rele
            if rele not in weigher_created[setup.name]["rele"]:
                weigher_created[setup.name]["rele"][rele] = 0
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
            cb_rele=self.Callback_Rele,
            cb_code_identify=self.Callback_WeighingByIdentify
        )
        weigher_name = instance.weigher_name
        is_changed_terminal = setup.terminal and setup.terminal != lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["terminal"]
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
        if setup.number_of_prints:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["number_of_prints"] = setup.number_of_prints
        if setup.report_on_in is not None:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["events"]["weighing"]["report"]["in"] = setup.report_on_in
        if setup.report_on_out is not None:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["events"]["weighing"]["report"]["out"] = setup.report_on_out
        if setup.max_theshold != -1:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["max_theshold"] = setup.max_theshold
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["printer_name"] = setup.printer_name
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["events"] = {
            "realtime": {
                "over_min": {
                    "set_rele": [rele.dict() for rele in setup.over_min]
                },
                "under_min": {
                    "set_rele": [rele.dict() for rele in setup.under_min]
                }
            },
            "weighing": {
                "report": {
                    "in": setup.report_on_in if setup.report_on_in is not None else False,
                    "out": setup.report_on_out if setup.report_on_out is not None else False
                },
                "set_rele": [rele.dict() for rele in setup.weighing],
                "cams": [{"picture": str(cam.picture), "live": str(cam.live), "active": cam.active} for cam in setup.cams]
            }
        }
        reles = setup.over_min + setup.under_min + setup.weighing
        number_reles = [rele.rele for rele in reles]
        config_json_reles = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["rele"].copy()
        for key, value in config_json_reles.items():
            if key not in number_reles:
                del lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["rele"][key]
        for obj in reles:
            rele = obj.rele
            if rele not in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["rele"] or is_changed_terminal:
                lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["rele"][rele] = 0
        response[weigher_name]["printer_name"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["printer_name"]
        response[weigher_name]["number_of_prints"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["number_of_prints"]
        response[weigher_name]["max_theshold"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["max_theshold"]
        response[weigher_name]["events"] = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][weigher_name]["events"]
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

    async def GetInstanceWeigherEndpoint(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        user = get_data_by_attribute("user", "username", "camcaptureplate")
        user["date_created"] = user["date_created"].isoformat()
        token = create_access_token(user)
        # Crea una connessione fittizia per determinare l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0] if len(s.getsockname()) > 0 else "127.0.0.1"
        s.close()
        return f"http://{ip}/api/command-weigher{self.url_weighing_auto}?instance_name={instance.instance_name}&weigher_name={instance.weigher_name}&token={token}"

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