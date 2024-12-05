from pydantic import BaseModel
from typing import Optional
from applications.utils.web_socket import ConnectionManager
from fastapi import Depends, HTTPException
import modules.md_weigher.md_weigher as md_weigher

class InstanceNameDTO(BaseModel):
	name: str

class InstanceNameNodeDTO(InstanceNameDTO):
	node: Optional[str] = None

class NodeConnectionManager:
	def __init__(self):
		self.manager_realtime = ConnectionManager()
		self.manager_diagnostic = ConnectionManager()

def get_query_params_name(params: InstanceNameDTO = Depends()):
	if params.name not in md_weigher.module_weigher.getAllInstance():
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	return params

def get_query_params_name_node(params: InstanceNameNodeDTO = Depends()):
	if params.name not in md_weigher.module_weigher.getAllInstance():
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	n = md_weigher.module_weigher.getInstanceNode(name=params.name, node=params.node)
	if md_weigher.module_weigher.getInstanceNode(name=params.name, node=params.node) is None:
		raise HTTPException(status_code=404, detail='Node not exist')
	return params