from pydantic import BaseModel
from libs.lb_database import CustomerDTOInit, SupplierDTOInit, VehicleDTOInit, MaterialDTOInit, update_data
from typing import Union, Optional

class DataInExecution(BaseModel):
	customer: CustomerDTOInit = CustomerDTOInit(**{})
	supplier: SupplierDTOInit = SupplierDTOInit(**{})
	vehicle: VehicleDTOInit = VehicleDTOInit(**{})
	material: MaterialDTOInit = MaterialDTOInit(**{})
	note: Union[str, None] = None

	def setAttribute(self, source):
		# Per ogni chiave dei nuovi dati passati controlla se è un oggetto o None
		for key, value in vars(source).items():

			if isinstance(value, str):
				if value in ["", "undefined", -1]:
					value = None
				setattr(self, key, value)
			elif isinstance(value, object) and value is not None:

				current_attr = getattr(self, key)
				current_id = getattr(current_attr, 'id')
				source_value_id = getattr(value, 'id')
				# Verifica se `source` ha qualsiasi altro attributo diverso da `id`
				other_source_values = any(sub_key != 'id' for sub_key in vars(source).keys())

				# Preparazione dei dati correnti prima di aggiungere le modifiche
				# Serve per gestire il cambio di selected sul database nel caso fosse in uso una anagrafica del database
				# Se l'id corrente è un numero
				if isinstance(current_id, int):
					# Controlla se é stato passato un nuovo id e se oltre a quello sono stati passati altri valori
					if source_value_id is None and other_source_values:
						# Se ci sono altri attributi, resetta tutti gli attributi correnti a None
						for sub_key, sub_value in vars(current_attr).items():
							setattr(current_attr, sub_key, None)
					# Setta l'id corrente nel database a selected False siccome è stato cambiato passando l'id, o altri attributi o entrambi
					update_data(key, current_id, {"selected": False})

				# Modifica dei valori
				for sub_key, sub_value in vars(value).items():
					if sub_value is not None or current_id is not None:
						# Se il valore è un tipo primitivo, aggiorna il nuovo valore
						if sub_value in ["", "undefined", -1]:
							sub_value = None
						setattr(current_attr, sub_key, sub_value)

	def deleteAttribute(self):
		# Per ogni chiave dei dati correnti
		for key, attr in vars(self).items():
			if isinstance(attr, str):
				setattr(self, key, None)
			elif isinstance(attr, object):
				if hasattr(attr, 'id'):
					# Ottiene l'id corrente dell'oggetto inerente alla chiave
					current_attr_id = getattr(attr, 'id')
					# Se l'id corrente non é None allora setta selected False dell'id sul database
					if current_attr_id is not None:
						update_data(key, current_attr_id, {"selected": False})
				if hasattr(attr, '__dict__'):
					# Resetta tutti gli attributi dell'oggetto corrente a None
					for sub_key, sub_value in attr.__dict__.items():
						setattr(attr, sub_key, None)

class IdSelected(BaseModel):
	id: Optional[int] = None

	def setAttribute(self, new_id):
		if new_id is not None:
			if new_id == -1:
				new_id = None
			if hasattr(self, 'id') and getattr(self, 'id') is not None:
				current_id = getattr(self, 'id')
				update_data('weighing', current_id, {"selected": False})
			setattr(self, 'id', new_id)
	
	def deleteAttribute(self):
		if hasattr(self, 'id') and getattr(self, 'id') is not None:
			current_id = getattr(self, 'id')
			update_data('weighing', current_id, {"selected": False})
		setattr(self, 'id', None)

class Data(BaseModel):
	data_in_execution: DataInExecution = DataInExecution(**{})
	id_selected: IdSelected = IdSelected(**{})