import modules.md_weigher.md_weigher as md_weigher
import asyncio
from applications.utils.utils_weigher import NodeConnectionManager
from typing import Union
from modules.md_weigher.types import Realtime, Weight
import libs.lb_config as lb_config
from libs.lb_database import add_data, get_data_by_id, update_data
import datetime as dt
import libs.lb_log as lb_log
from applications.router.weigher.types import Data, DataInExecution, IdSelected

class CallbackWeigher:
    def __init__(self):
        self.weighers_data = {}

        md_weigher.module_weigher.initializeModuleConfig(config=lb_config.g_config["app_api"]["weighers"])

        for instance_name, instance in md_weigher.module_weigher.instances.items():
            nodes_sockets = {}
            for weigher_name, weigher in instance.nodes.items():
                nodes_sockets[weigher_name] = {
                    "sockets": NodeConnectionManager(),
                    "data": Data(**lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"])
                }
            self.weighers_data[instance_name] = nodes_sockets

        md_weigher.module_weigher.setApplicationCallback(
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic, 
            cb_weighing=self.Callback_Weighing, 
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_action_in_execution=self.Callback_ActionInExecution
        )

    def addInstanceSocket(self, instance_name: str):
        self.weighers_data[instance_name] = {}

    def deleteInstanceSocket(self, instance_name: str):
        for node in self.weighers_data[instance_name]:
            self.weighers_data[instance_name][node]["sockets"].manager_realtime.disconnect_all()
            self.weighers_data[instance_name][node]["sockets"].manager_realtime = None
            self.weighers_data[instance_name][node]["sockets"].manager_diagnostic.disconnect_all()
            self.weighers_data[instance_name][node]["sockets"].manager_diagnostic = None
            self.weighers_data[instance_name][node]["data"].data_in_execution.deleteAttribute()
            self.weighers_data[instance_name][node]["data"].id_selected.deleteAttribute()
        self.weighers_data.pop(instance_name)

    def addInstanceWeigherSocket(self, instance_name: str, weigher_name: str, data: Data):
        node_sockets = {
            "sockets": NodeConnectionManager(),
            "data": data
        }
        self.weighers_data[instance_name][weigher_name] = node_sockets

    def deleteInstanceWeigherSocket(self, instance_name: str, weigher_name: str):
        self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.disconnect_all()
        self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime = None
        self.weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.disconnect_all()
        self.weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic = None
        self.weighers_data[instance_name].pop(weigher_name)

    # ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
    # Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
    def Callback_Realtime(self, instance_name: str, weigher_name: Union[str, None], pesa_real_time: Realtime):
        asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(pesa_real_time.dict()))

    # Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
    def Callback_Diagnostic(self, instance_name: str, weigher_name: Union[str, None], diagnostic: dict):
        asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(diagnostic))

    # Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
    def Callback_Weighing(self, instance_name: str, weigher_name: Union[str, None], last_pesata: Weight):
        if last_pesata.weight_executed.executed:
            if isinstance(last_pesata.data_assigned, DataInExecution):
                node = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance_name,weigher_name=weigher_name)
                obj = {
                    "plate": last_pesata.data_assigned.vehicle.plate,
                    "vehicle": last_pesata.data_assigned.vehicle.name,
                    "customer": last_pesata.data_assigned.customer.name, 
                    "customer_cell": last_pesata.data_assigned.customer.cell,
                    "customer_cfpiva": last_pesata.data_assigned.customer.cfpiva,
                    "supplier": last_pesata.data_assigned.supplier.name,
                    "supplier_cell": last_pesata.data_assigned.supplier.cell,
                    "supplier_cfpiva": last_pesata.data_assigned.supplier.cfpiva,
                    "material": last_pesata.data_assigned.material.name,
                    "note": last_pesata.data_assigned.note,
                    "weight1": last_pesata.weight_executed.gross_weight,
                    "weight2": None if last_pesata.weight_executed.tare == '0' else last_pesata.weight_executed.tare,
                    "net_weight": last_pesata.weight_executed.net_weight,
                    "date1": None if last_pesata.weight_executed.tare != '0' else dt.datetime.now(),
                    "date2": None if last_pesata.weight_executed.tare == '0' else dt.datetime.now(),
                    "card_code": None,
                    "card_number": None,
                    "pid1": None if last_pesata.weight_executed.tare != '0' else last_pesata.weight_executed.pid,
                    "pid2": None if last_pesata.weight_executed.tare == '0' else last_pesata.weight_executed.pid,
                    "weigher": weigher_name
                }
                if last_pesata.image1 is not None:
                    image1 = add_data("image_captured", last_pesata.image1.dict())
                    obj["in_image_captured1_id"] = image1.id                  
                    del last_pesata.image1
                if last_pesata.image2 is not None:
                    image2 = add_data("image_captured", last_pesata.image2.dict())
                    obj["in_image_captured2_id"] = image2.id
                    del last_pesata.image2
                if last_pesata.image3 is not None:
                    image3 = add_data("image_captured", last_pesata.image3.dict())
                    obj["in_image_captured3_id"] = image3.id
                    del last_pesata.image3
                if last_pesata.image4 is not None:
                    image4 = add_data("image_captured", last_pesata.image4.dict())
                    obj["in_image_captured4_id"] = image4.id
                    del last_pesata.image4
                add_data("weighing", obj)
                self.weighers_data[instance_name][weigher_name]["data"].data_in_execution.deleteAttribute()
                data = self.weighers_data[instance_name][weigher_name]["data"].dict()
                lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"] = data["data_in_execution"]
                lb_config.saveconfig()
                asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(data))
            elif isinstance(last_pesata.data_assigned, int) and last_pesata.weight_executed.executed:
                lb_log.warning("2")
                data = get_data_by_id("weighing", last_pesata.data_assigned)
                net_weight = data["weight1"] - int(last_pesata.weight_executed.gross_weight)
                obj = {
                    "weight2": last_pesata.weight_executed.gross_weight,
                    "net_weight": net_weight,
                    "date2": dt.datetime.now(),
                    "pid2": last_pesata.weight_executed.pid
                }
                if last_pesata.image1 is not None:
                    image1 = add_data("image_captured", last_pesata.image1.dict())
                    obj["out_image_captured2_id"] = image1.id
                    del last_pesata.image1
                if last_pesata.image2 is not None:
                    image2 = add_data("image_captured", last_pesata.image2.dict())
                    obj["out_image_captured2_id"] = image2.id
                    del last_pesata.image2
                if last_pesata.image3 is not None:
                    image3 = add_data("image_captured", last_pesata.image3.dict())
                    obj["out_image_captured3_id"] = image3.id
                    del last_pesata.image3
                if last_pesata.image4 is not None:
                    image4 = add_data("image_captured", last_pesata.image4.dict())
                    obj["out_image_captured4_id"] = image4.id
                    del last_pesata.image4
                update_data("weighing", last_pesata.data_assigned, obj)
                self.weighers_data[instance_name][weigher_name]["data"].id_selected.setAttribute(-1)
                data = self.weighers_data[instance_name][weigher_name]["data"].dict()
                lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"] = data["id_selected"]
                lb_config.saveconfig()
                asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(data))
            elif last_pesata.data_assigned is None and last_pesata.weight_executed.executed:
                node = md_weigher.module_weigher.instances[instance_name].getNode(weigher_name)
                obj = {
                    "plate": None,
                    "vehicle": None,
                    "customer": None, 
                    "customer_cell": None,
                    "customer_cfpiva": None,
                    "supplier": None,
                    "supplier_cell": None,
                    "supplier_cfpiva": None,
                    "material": None,
                    "note": None,
                    "weight1": last_pesata.weight_executed.gross_weight,
                    "weight2": None if last_pesata.weight_executed.tare == '0' else last_pesata.weight_executed.tare,
                    "net_weight": last_pesata.weight_executed.net_weight,
                    "date1": None,
                    "date2": dt.datetime.now(),
                    "card_code": None,
                    "card_number": None,
                    "pid1": None,
                    "pid2": last_pesata.weight_executed.pid,
                    "weigher": weigher_name
                }
                if last_pesata.image1 is not None:
                    image1 = add_data("image_captured", last_pesata.image1.dict())
                    obj["out_image_captured1_id"] = image1.id
                    del last_pesata.image1
                if last_pesata.image2 is not None:
                    image2 = add_data("image_captured", last_pesata.image2.dict())
                    obj["out_image_captured2_id"] = image2.id
                    del last_pesata.image2
                if last_pesata.image3 is not None:
                    image3 = add_data("image_captured", last_pesata.image3.dict())
                    obj["out_image_captured3_id"] = image3.id
                    del last_pesata.image3
                if last_pesata.image4 is not None:
                    image4 = add_data("image_captured", last_pesata.image4.dict())
                    obj["out_image_captured4_id"] = image4.id
                    del last_pesata.image4
                add_data("weighing", obj)
        asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(last_pesata.dict()))

    def Callback_TarePTareZero(self, instance_name: str, weigher_name: Union[str, None], ok_value: str):
        result = {"command_executed": ok_value}
        asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))

    def Callback_ActionInExecution(self, instance_name: str, weigher_name: Union[str, None], action_in_execution: str):
        result = {"command_in_executing": action_in_execution}
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
        
    def Callback_Rele(self, instance_name: str, weigher_name: Union[str, None], port_rele: tuple):
        key, value = port_rele
        result = {"rele": key, "status": value}
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))