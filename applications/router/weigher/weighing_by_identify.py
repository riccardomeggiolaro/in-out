from fastapi import Request, Depends, HTTPException
from applications.router.weigher.dto import IdentifyDTO, DataDTO
from modules.md_database.functions.get_reservation_by_plate_if_uncomplete import get_reservation_by_plate_if_uncomplete
from modules.md_database.functions.get_reservation_by_identify_if_uncomplete import get_reservation_by_identify_if_uncomplete
from modules.md_database.interfaces.reservation import AddReservationDTO, VehicleDataDTO
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
import libs.lb_config as lb_config
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
import asyncio
from modules.md_weigher import md_weigher

async def WeighingByIdentify(self, request: Request, identify_dto: IdentifyDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
    try:
        reservation = None
        if lb_config.g_config["app_api"]["use_badge"]:
            reservation = get_reservation_by_identify_if_uncomplete(identify=identify_dto.identify)
        else:
            reservation = get_reservation_by_plate_if_uncomplete(plate=identify_dto.identify)
        allow_white_list = lb_config.g_config["app_api"]["use_white_list"]
        if not reservation and allow_white_list:
            vehicle = get_data_by_attributes("vehicle", {type: identify_dto.identify})
            if vehicle and vehicle["white_list"]:
                data = AddReservationDTO(**{
                    "vehicle": VehicleDataDTO(**vehicle)
                })
                reservation = await self.addReservation(request=None, body=AddReservationDTO(**{
                        **data.dict(),
                        "number_in_out": 1,
                        "type": "RESERVATION",
                        "hidden": False
                    }))
                reservation = reservation.dict() if reservation else reservation
        if reservation:
            current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
            specific = "telecamera " if request.state.user.level == 0 else ""
            if current_weigher_data["id_selected"]["id"] != reservation["id"]:
                self.Callback_Message(instance_name=instance.instance_name, weigher_name=instance.weigher_name, message=f"'{identify_dto.identify}' selezionata da {specific}'{request.client.host}'")
                await self.SetData(data_dto=DataDTO(**{"id_selected": {"id": reservation["id"]}}), instance=instance)
                await asyncio.sleep(1)
            status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
                instance_name=instance.instance_name, 
                weigher_name=instance.weigher_name, 
                modope="WEIGHING", 
                data_assigned=reservation["id"])
            if error_message:
                error_message = f"Errore effettuando pesata da {specific}'{request.client.host}': {error_message}"
                self.Callback_Message(instance_name=instance.instance_name, weigher_name=instance.weigher_name, message=error_message)
            return {
                "instance": instance,
                "command_details": {
                    "status_modope": status_modope,
                    "command_executed": command_executed,
                    "error_message": error_message
                },
                "reservation_id": reservation["id"]
            }
        raise HTTPException(status_code=404, detail=f"Reservation not found for plate '{identify_dto.identify}'")
    except Exception as e:
        status_code = getattr(e, 'status_code', 400)
        detail = getattr(e, 'detail', str(e))
        raise HTTPException(status_code=status_code, detail=detail)