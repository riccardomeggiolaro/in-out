import modules.md_weigher.md_weigher as md_weigher
import asyncio
from applications.utils.instance_weigher import NodeConnectionManager
from typing import Union
from modules.md_weigher.types import Realtime, Weight, Data
import libs.lb_config as lb_config
from libs.lb_database import add_data, get_data_by_id, update_data
import datetime as dt

class CallbackWeigher:
    def __init__(self):
        self.weighers_sockets = {}

        for name, instance in md_weigher.module_weigher.instances.items():
            nodes_sockets = {}
            for node in instance.nodes:
                nodes_sockets[node.node] = NodeConnectionManager()
            self.weighers_sockets[name] = nodes_sockets

        md_weigher.module_weigher.setApplicationCallback(
            cb_realtime=self.Callback_Realtime, 
            cb_diagnostic=self.Callback_Diagnostic, 
            cb_weighing=self.Callback_Weighing, 
            cb_tare_ptare_zero=self.Callback_TarePTareZero,
            cb_data=self.Callback_Data,
            cb_action_in_execution=self.Callback_ActionInExecution
        )

    # ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
    # Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
    def Callback_Realtime(self, instance_name: str, instance_node: Union[str, None], pesa_real_time: Realtime):
        pesa_real_time.net_weight = pesa_real_time.net_weight.zfill(6)
        pesa_real_time.tare = pesa_real_time.tare.zfill(6)
        asyncio.run(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(pesa_real_time.dict()))

    # Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
    def Callback_Diagnostic(self, instance_name: str, instance_node: Union[str, None], diagnostic: dict):
        asyncio.run(self.weighers_sockets[instance_name][instance_node].manager_diagnostic.broadcast(diagnostic))

    # Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
    def Callback_Weighing(self, instance_name: str, instance_node: Union[str, None], last_pesata: Weight):
        # global printer
        if last_pesata.data_assigned is not None and not isinstance(last_pesata.data_assigned, int) and last_pesata.weight_executed.executed:
            node = md_weigher.module_weigher.instances[instance_name].getNode(instance_node)
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
                "weigher": node["name"]
            }
            add_data("weighing", obj)
            status, data = md_weigher.module_weigher.instances[instance_name].deleteDataInExecution(node=instance_node, call_callback=False)
            node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"] if n["node"] == instance_node]
            index_node_found = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"].index(node_found[0])
            lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][index_node_found]["data"]["data_in_execution"] = data["data_in_execution"]
            lb_config.saveconfig()
            asyncio.run(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data))
        elif isinstance(last_pesata.data_assigned, int) and last_pesata.weight_executed.executed:
            data = get_data_by_id("weighing", last_pesata.data_assigned)
            net_weight = data["weight1"] - int(last_pesata.weight_executed.gross_weight)
            obj = {
                "weight2": last_pesata.weight_executed.gross_weight,
                "net_weight": net_weight,
                "date2": dt.datetime.now(),
                "pid2": last_pesata.weight_executed.pid
            }
            update_data("weighing", last_pesata.data_assigned, obj)
            status, data = md_weigher.module_weigher.instances[instance_name].setIdSelected(node=instance_node, new_id=-1, call_callback=False)
            node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"] if n["node"] == instance_node]
            index_node_found = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"].index(node_found[0])
            lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][index_node_found]["data"]["id_selected"] = {
                "id": None
            }
            lb_config.saveconfig()
            asyncio.run(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data))
        elif last_pesata.data_assigned is None and last_pesata.weight_executed.executed:
            node = md_weigher.module_weigher.instances[instance_name].getNode(instance_node)
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
                "weigher": node["name"]
            }
            add_data("weighing", obj)
        # if last_pesata.weight_executed.executed:
        # 	html = f"""
        # 		<h1>PESATA ESEGUITA</h1>
        # 		<p>PID: {last_pesata.weight_executed.pid}</p>
        # 		<p>PESO: {last_pesata.weight_executed.gross_weight}</p>
        # 	"""
        # 	printer.print_html(html)

        asyncio.run(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(last_pesata.dict()))

    def Callback_TarePTareZero(self, instance_name: str, instance_node: Union[str, None], ok_value: str):
        result = {"command_executend": ok_value}
        asyncio.run(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(result))

    def Callback_Data(self, instance_name: str, instance_node: Union[str, None], data: Data):
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data.dict()))
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data.dict()))

    def Callback_ActionInExecution(self, instance_name: str, instance_node: Union[str, None], action_in_execution: str):
        result = {"command_in_executing": action_in_execution}
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(result))
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(result))