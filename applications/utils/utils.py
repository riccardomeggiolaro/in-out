from fastapi import Request, Depends, HTTPException
from typing import Dict, Union
from applications.utils.instance_weigher import InstanceNameDTO, InstanceNameNodeDTO
import modules.md_weigher.md_weigher as md_weigher
import libs.lb_log as lb_log

async def get_query_params(request: Request) -> Dict[str, Union[str, int]]:
	"""
	Converts URL query parameters into a dictionary
	"""
	return dict(request.query_params)

def get_query_params_name(params: InstanceNameDTO = Depends()):
	if params.name not in md_weigher.module_weigher.instances:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	return params

def get_query_params_name_node(params: InstanceNameNodeDTO = Depends()):
	lb_log.warning(params)
	if params.name not in md_weigher.module_weigher.instances:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	if md_weigher.module_weigher.instances[params.name].getNode(params.node) is None:
		raise HTTPException(status_code=404, detail='Node not exist')
	return params