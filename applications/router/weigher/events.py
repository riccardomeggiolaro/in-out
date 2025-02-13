from fastapi import APIRouter, Depends, HTTPException
import libs.lb_config as lb_config
from applications.router.weigher.dto import CamEventDTO, ReleEventDTO
from applications.utils.utils_weigher import InstanceNameDTO, InstanceNameWeigherDTO, get_query_params_name, get_query_params_name_node

class EventsRouter:
    def __init__(self):
        self.router_events = APIRouter()

        self.router_events.add_api_route('/list', self.GetListEvents, methods=['GET'])        
        self.router_events.add_api_route('/cam/add', self.AssignCamEvent, methods=['POST'])
        self.router_events.add_api_route('/cam/delete', self.DeleteCamEvent, methods=['DELETE'])
        self.router_events.add_api_route('/rele/add', self.AssignReleEvent, methods=['POST'])
        self.router_events.add_api_route('/rele/delete', self.DeleteReleEvent, methods=['DELETE'])

    async def GetListEvents(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        return lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]

    async def AssignCamEvent(self, camEvent: CamEventDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        if camEvent.cam not in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"]:
            raise HTTPException(status_code=404, detail="Cam not exist")
        key = None
        if camEvent.event in ["over_min", "under_min"]:
            key = "realtime"
        elif camEvent.event in ["weight1", "weight2"]:
            key = "weighing"
        if camEvent.cam in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][camEvent.event]["take_picture"]:
            raise HTTPException(status_code=400, detail="Cam name just exist in the event")
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][camEvent.event]["take_picture"].append(camEvent.cam)
        lb_config.saveconfig()
        return lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][camEvent.event]["take_picture"]

    async def DeleteCamEvent(self, camEvent: CamEventDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        key = None
        if camEvent.event in ["over_min", "under_min"]:
            key = "realtime"
        elif camEvent.event in ["weight1", "weight2"]:
            key = "weighing"
        if camEvent.cam in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][camEvent.event]["take_picture"]:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][camEvent.event]["take_picture"].remove(camEvent.cam)
            lb_config.saveconfig()
            return { "deleted": True }
        raise HTTPException(status_code=404, detail="Cam name not exist in the event")

    async def AssignReleEvent(self, releEvent: ReleEventDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        if releEvent.rele.name not in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["list_port_rele"]:
            raise HTTPException(status_code=404, detail="Rele not exist")
        key = None
        if releEvent.event in ["over_min", "under_min"]:
            key = "realtime"
        elif releEvent.event in ["weight1", "weight2"]:
            key = "weighing"
        rele_configuration = {releEvent.rele.name: releEvent.rele.status}
        if rele_configuration in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][releEvent.event]["set_rele"]:
            raise HTTPException(status_code=400, detail="Rele configuration just exist in the event")            
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][releEvent.event]["set_rele"].append(rele_configuration)
        lb_config.saveconfig()
        return lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][releEvent.event]["set_rele"]
    
    async def DeleteReleEvent(self, releEvent: ReleEventDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        key = None
        if releEvent.event in ["over_min", "under_min"]:
            key = "realtime"
        elif releEvent.event in ["weight1", "weight2"]:
            key = "weighing"
        rele_configuration = {releEvent.rele.name: releEvent.rele.status}
        if rele_configuration in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][releEvent.event]["set_rele"]:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"][key][releEvent.event]["set_rele"].remove(rele_configuration)
            lb_config.saveconfig()
            return { "deleted": True }
        raise HTTPException(status_code=404, detail="Rele configuration not exist in the event")