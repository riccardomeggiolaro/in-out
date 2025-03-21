from fastapi import APIRouter, Depends, HTTPException
import libs.lb_config as lb_config
from applications.router.weigher.dto import CamEventDTO, ReleEventDTO
from applications.utils.utils_weigher import InstanceNameDTO, InstanceNameWeigherDTO, get_query_params_name, get_query_params_name_node

class ReleRouter:
	def __init__(self):
		self.router_rele = APIRouter()