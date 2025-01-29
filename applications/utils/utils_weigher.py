from pydantic import BaseModel
from typing import Optional
from applications.utils.web_socket import ConnectionManager
from fastapi import Depends, HTTPException
import modules.md_weigher.md_weigher as md_weigher

class InstanceNameDTO(BaseModel):
	instance_name: str

class InstanceNameWeigherDTO(InstanceNameDTO):
	weigher_name: Optional[str] = None

class NodeConnectionManager:
	def __init__(self):
		self.manager_realtime = ConnectionManager()
		self.manager_diagnostic = ConnectionManager()

def get_query_params_name(params: InstanceNameDTO = Depends()):
	if params.instance_name not in md_weigher.module_weigher.getAllInstance():
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	return params

def get_query_params_name_node(params: InstanceNameWeigherDTO = Depends()):
	if params.instance_name not in md_weigher.module_weigher.getAllInstance():
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	if params.weigher_name not in md_weigher.module_weigher.getAllInstanceWeigher(instance_name=params.instance_name):
		raise HTTPException(status_code=404, detail='Name weigher not exist')
	return params