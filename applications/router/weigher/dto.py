from libs.lb_utils import CustomBaseModel
from libs.lb_database import CustomerDTO, SupplierDTO, VehicleDTO, MaterialDTO, get_data_by_id
from typing import Optional
from pydantic import root_validator, validator, BaseModel
from applications.router.weigher.types import DataInExecution

class DataInExecutionDTO(CustomBaseModel):
	customer: Optional[CustomerDTO] = CustomerDTO(**{})
	supplier: Optional[SupplierDTO] = SupplierDTO(**{})
	vehicle: Optional[VehicleDTO] = VehicleDTO(**{})
	material: Optional[MaterialDTO] = MaterialDTO(**{})
	note: Optional[str] = None

	@root_validator(pre=True)
	def check_only_one_attribute_set(cls, values):
		# Contiamo quanti dei 5 attributi opzionali sono impostati
		non_null_values = sum(1 for key, value in values.items() if value is not None)

		if non_null_values > 1:
			raise ValueError("Solo uno dei seguenti attributi deve essere presente: customer, supplier, vehicle, material, note.")

		return values

class IdSelectedDTO(CustomBaseModel):
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('weighing', v, True, True)
			if not data:
				raise ValueError('Id not exist in weighings')
		return v

class DataDTO(BaseModel):
    data_in_execution: Optional[DataInExecutionDTO] = DataInExecutionDTO(**{})
    id_selected: Optional[IdSelectedDTO] = IdSelectedDTO(**{})

class WeighingDataDTO(CustomBaseModel):
	id_selected: Optional[int] = None
	plate: Optional[str] = None
	data_in_execution: Optional[DataInExecution] = None

	@root_validator(pre=True)
	def check_only_one_attribute_set(cls, values):
		# Contiamo quanti dei 5 attributi opzionali sono impostati
		non_null_values = sum(1 for key, value in values.items() if value is not None)

		if non_null_values > 1:
			raise ValueError("Solo uno dei seguenti attributi deve essere presente: id o plate.")

		return values