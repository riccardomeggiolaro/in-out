from fastapi import APIRouter, Depends
from applications.utils.utils import get_query_params_name_node
import modules.md_weigher.md_weigher as md_weigher
import libs.lb_config as lb_config
from modules.md_weigher.types import DataInExecution
from modules.md_weigher.dto import DataDTO
from applications.utils.instance_weigher import InstanceNameNodeDTO

router = APIRouter()

@router.get("/data_in_execution")
async def GetDataInExecution(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
    status, data = md_weigher.module_weigher.instances[instance.name].getData(node=instance.node)
    return {
        "instance": instance,
        "data": data,
        "status": status
    }

@router.patch("/data_in_execution")
async def SetDataInExecution(data_dto: DataDTO, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
    data_in_execution = DataInExecution(**data_dto.data_in_execution.dict())
    status, data = md_weigher.module_weigher.instances[instance.name].setDataInExecution(node=instance.node, data_in_execution=data_in_execution, call_callback=True)
    if data_dto.id_selected is not None:
        status, data = md_weigher.module_weigher.instances[instance.name].setIdSelected(node=instance.node, new_id=data_dto.id_selected.id, call_callback=True)
    node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
    index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
    lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data"] = data
    lb_config.saveconfig()
    return {
        "instance": instance,
        "data": data,
        "status": status
    }

@router.delete("/data_in_execution")
async def DeleteDataInExecution(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
    status, data = md_weigher.module_weigher.instances[instance.name].deleteDataInExecution(node=instance.node, call_callback=True)
    node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
    index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
    lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data"]["data_in_execution"] = data
    lb_config.saveconfig()
    return {
        "instance": instance,
        "data": data,
        "status": status
    }