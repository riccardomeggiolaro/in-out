from fastapi import APIRouter, Depends, HTTPException
import libs.lb_config as lb_config
from applications.utils.utils_weigher import InstanceNameDTO, InstanceNameWeigherDTO, get_query_params_name, get_query_params_name_node
from applications.router.weigher.dto import CamDTO, SetCamDTO, CamEventDTO, ReleEventDTO

class CamsRouter:
    def __init__(self):
        self.router_cams = APIRouter()