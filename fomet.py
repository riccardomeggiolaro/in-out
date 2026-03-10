	async def WeighingByIdentify(self, request: Request, identify_dto: IdentifyDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), token: str = None, notify_identify_code: bool = True):
		response = get_user(token=token)
		if hasattr(response, "status_code"):
			return response
		if not request:
			request = Request({
				"type": "http",
				"headers": [],
				"client": (response.username, response.level)
			})
		request.state.user = response
		mode = lb_config.g_config["app_api"]["mode"]
		error_message = None
		success_message = None
		access = None
		proc = {
			"instance_name": instance.instance_name,
			"weigher_name": instance.weigher_name,
			"identify": identify_dto.identify
		}
		cam_message = f'"{identify_dto.identify}"'
		if request is not None:
			cam_message = cam_message + f" ricevuto da {request.client.host}"
		else:
			cam_message = cam_message + f" ricevuto da terminale"
		if len(identify_dto.identify) < 5:
			error_message = "L'identificativo deve essere di almeno 5 caratteri"
		else:
			if notify_identify_code:
				await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"cam_message": cam_message})
			existing_proc = next(
				(p for p in self.automatic_weighing_process if p["instance_name"] == instance.instance_name and p["weigher_name"] == instance.weigher_name),
				None
			)
			# current_data = await self.GetData(instance=instance)
			if mode == "MANUALLY":
				error_message = f"Modalità automatica disattiva. Tentativo di pesatura {cam_message} bloccato"
			elif existing_proc:
				error_message = f"Pesatura automatica già in esecuzione sulla pesa '{instance.weigher_name}' con identify '{existing_proc['identify']}'."
			# elif Data(**{}) != Data(**current_data):
			# 	error_message = f"Sulla pesa '{instance.weigher_name}' sono già presenti dati in esecuzione. Attendi che gli operatori completino le operazioni manuali prima di avviare una nuova pesatura automatica."
			else:
				weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
				division = weigher["division"]
				take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
				take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
				if take_of_weight_on_startup is True:
					error_message = "Scaricare la pesa dopo l'avvio del programma"
				elif take_of_weight_before_weighing is True:
					error_message = "Scaricare la pesa prima di eseguire nuova pesata"
				else:
					access = get_access_by_identify_if_uncomplete(identify=identify_dto.identify)
					realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
					min_weight = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["min_weight"]
					if realtime.gross_weight == "" or realtime.gross_weight != "" and float(realtime.gross_weight) < min_weight:
						error_message = f"Il peso deve essere maggiore di {min_weight} kg"
					elif access:
						current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
						if current_weigher_data["id_selected"]["id"] != access["id"]:
							await self.DeleteData(instance=instance)
							try:
								if access["type"].name == TypeAccess.RESERVATION.name and access["number_in_out"] is not None and realtime.tare != "0":
									error_message = "Non è possibile effettuare pesate con tara negli accessi multipli."
								else:
									data_dto = DataDTO(**{"id_selected": {"id": access["id"]}})
									need_to_confirm = True if mode == "SEMIAUTOMATIC" else False
									await self.SetData(request=None, data_dto=data_dto, instance=instance, need_to_confirm=need_to_confirm)
							except Exception as e:
								error_message = e.detail
						if not error_message:
							self.automatic_weighing_process.append(proc)
							if mode == "AUTOMATIC":
								async def handleAutomatic():
									data = weighers_data[instance.instance_name][instance.weigher_name]["data"]
									tare = data["data_in_execution"]["vehicle"]["tare"]
									weight1 = data["id_selected"]["weight1"]
									timeout = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["connection"]["timeout"]
									time_between_actions = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["time_between_actions"]
									stable = 0
									while True:
										await asyncio.sleep(time_between_actions)
										timeout = timeout - time_between_actions
										current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										modope = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_modope = md_weigher.module_weigher.getCurrentModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_tare = realtime.tare.replace("PT", "").replace(" ",  "")
										m = modope if request is not None else current_modope
										if modope != "PRESETTARE" and current_modope != "PRESETTARE":
											if current_weigher_data["id_selected"]["id"] != access["id"]:
												error_message = f"Pesatura automatica interrotta. Accesso con '{identify_dto.identify}' deselezionato."
												await self.DeleteData(instance=instance)
												await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
												break
											if weight1 is None and current_tare != "" and tare is not None and abs(float(current_tare) - float(tare)) > division:
												if current_tare == "0":
													if timeout >= 0:
														message = f"Impostando la tara per la pesatura automatica."
														await self.DeleteData(instance=instance)
														await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"message": message})
												elif timeout >= 0:
													error_message = f"Pesatura automatica interrotta. La tara di {tare} kg non è stata impostata correttamente."
													await self.DeleteData(instance=instance)
													await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
													break
											elif realtime.gross_weight == "" or float(realtime.gross_weight) != "" and float(realtime.gross_weight) < min_weight:
												error_message = f"Pesatura automatica interrotta. Il peso deve essere maggiore di {min_weight} kg."
												await self.DeleteData(instance=instance)
												await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
												break
											elif realtime.gross_weight != "" and float(realtime.gross_weight) >= min_weight:
												if realtime.status == "ST":
													if stable == 3:
														data_assigned = DataAssignedDTO(**{"accessId": access["id"], "userId": request.state.user.id, "mode": "AUTOMATIC", "token": token, "identify_code": identify_dto.identify})
														status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
															instance_name=instance.instance_name, 
															weigher_name=instance.weigher_name, 
															modope="WEIGHING", 
															data_assigned=data_assigned)
														if error_message:
															error_message = f"Errore nella pesatura automatica: {error_message}. Ritento."
															await self.DeleteData(instance=instance)
															await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
														if command_executed:
															await self.DeleteData(instance=instance)
															break
													else:
														stable = stable + 1
												else:
													stable = 0
									# Rimuovi il processo dalla lista in modo sicuro
									self.automatic_weighing_process = [
										p for p in self.automatic_weighing_process
										if not (
											p["instance_name"] == instance.instance_name and
											p["weigher_name"] == instance.weigher_name and
											p["identify"] == identify_dto.identify
										)
									]
								threading.Thread(target=lambda: asyncio.run(handleAutomatic())).start()
								success_message = "Pesatura automatica presa in carico."
							elif mode == "SEMIAUTOMATIC":
								async def handleSemiautomatic():
									data = weighers_data[instance.instance_name][instance.weigher_name]["data"]
									tare = data["data_in_execution"]["vehicle"]["tare"]
									weight1 = data["id_selected"]["weight1"]
									timeout = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["connection"]["timeout"]
									time_between_actions = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["time_between_actions"]
									stable = 0
									while True:
										await asyncio.sleep(time_between_actions)
										timeout = timeout - time_between_actions
										current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										modope = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_modope = md_weigher.module_weigher.getCurrentModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_tare = realtime.tare.replace("PT", "").replace(" ",  "")
										m = modope if request is not None else current_modope

										if modope != "PRESETTARE" and current_modope != "PRESETTARE":
											if current_weigher_data["id_selected"]["id"] != access["id"]:
												break
											if weight1 is None and current_tare != "" and tare is not None and abs(float(current_tare) - float(tare)) > division:
												if current_tare == "0":
													if timeout >= 0:
														message = f"Impostando la tara per la pesatura semiautomatica."
														await self.DeleteData(instance=instance)
														await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"message": message})
												elif timeout >= 0:
													error_message = f"Pesatura semiautomatica interrotta. La tara di {tare} kg non è stata impostata correttamente."
													await self.DeleteData(instance=instance)
													await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
													break
											elif realtime.gross_weight == "" or float(realtime.gross_weight) != "" and float(realtime.gross_weight) < min_weight:
												error_message = f"Pesatura semiautomatica interrotta. Il peso deve essere maggiore di {min_weight} kg."
												await self.DeleteData(instance=instance)
												await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
												break
											elif realtime.gross_weight != "" and float(realtime.gross_weight) >= min_weight:
												if realtime.status == "ST":
													stable += 1
												else:
													stable = 0
									# Rimuovi il processo dalla lista in modo sicuro
									self.automatic_weighing_process = [
										p for p in self.automatic_weighing_process
										if not (
											p["instance_name"] == instance.instance_name and
											p["weigher_name"] == instance.weigher_name and
											p["identify"] == identify_dto.identify
										)
									]
								threading.Thread(target=lambda: asyncio.run(handleSemiautomatic())).start()
								error_message = "Pesatura semiautomatica in attesa di conferma dall'operatore."
					else:
						error_message = f"Accesso con '{identify_dto.identify}' non esistente."
		if error_message:
			error_message = cam_message + f" - Errore: {error_message}"
			await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"cam_message": error_message})
		elif success_message:
			success_message = cam_message + f" - {success_message}"
			if notify_identify_code:
				await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"cam_message": success_message})
		return {
			"message": error_message or success_message,
			"access_id": access["id"] if access else None,
			"identify_dto": identify_dto
		}