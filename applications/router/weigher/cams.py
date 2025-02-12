from fastapi import APIRouter, Depends, HTTPException
import libs.lb_config as lb_config
from applications.utils.utils_weigher import InstanceNameDTO, InstanceNameWeigherDTO, get_query_params_name, get_query_params_name_node
from applications.router.weigher.dto import CamDTO, SetCamDTO, CamEventDTO, ReleEventDTO
from applications.router.weigher.data_in_execution import DataInExecutionRouter

class CamsRouter:
    def __init__(self):
        self.router_cams = APIRouter()
        
        self.router_cams.add_api_route('/add', self.AddInstanceWeigherCam, methods=['POST'])
        self.router_cams.add_api_route('/set', self.SetIntanceWeigherCam, methods=['PATCH'])
        self.router_cams.add_api_route('/delete', self.DeleteInstanceWeigherCam, methods=['DELETE'])
        
    async def AddInstanceWeigherCam(self, cam: CamDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        if cam.name in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"]:
            raise HTTPException(status_code=400, detail="Name just exist")
        lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"][cam.name] = cam.url
        lb_config.saveconfig()
        return cam

    async def SetIntanceWeigherCam(self, cam: SetCamDTO, camName: str, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        if camName not in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"]:
            raise HTTPException(status_code=404, detail="Name not exist")
        if cam.url is not None:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"][camName] = cam.url
        if cam.name is not None:
            if cam.name in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"]:
                raise HTTPException(status_code=400, detail="Name just exist")
            url = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"][camName]
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"][cam.name] = url
            del lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"][camName]
            if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["over_min"]["take_picture"]:
                index = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["over_min"]["take_picture"].index(camName)
                lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["over_min"]["take_picture"][index] = cam.name
            if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["under_min"]["take_picture"]:
                index = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["under_min"]["take_picture"].index(camName)
                lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["under_min"]["take_picture"][index] = cam.name
            if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight1"]["take_picture"]:
                index = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight1"]["take_picture"].index(camName)
                lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight1"]["take_picture"][index] = cam.name
            if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight2"]["take_picture"]:
                index = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight2"]["take_picture"].index(camName)
                lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight2"]["take_picture"][index] = cam.name
            camName = cam.name
        lb_config.saveconfig()
        return {
            camName: lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"][camName]
        }

    async def DeleteInstanceWeigherCam(self, camName: str, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        if camName not in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"]:
            raise HTTPException(status_code=404, detail="Name not exist")
        del lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["cams"][camName]
        if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["over_min"]["take_picture"]:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["over_min"]["take_picture"].remove(camName)
        if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["under_min"]["take_picture"]:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["realtime"]["under_min"]["take_picture"].remove(camName)
        if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight1"]["take_picture"]:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight1"]["take_picture"].remove(camName)
        if camName in lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight2"]["take_picture"]:
            lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["weight2"]["take_picture"].remove(camName)
        lb_config.saveconfig()
        return { "deleted": True }