from modules.md_database.md_database import SessionLocal, Subject, Vector, Driver, Vehicle, Material, Access, AccessStatus, Weighing, Operator, TypeSubjectEnum
from modules.md_database.interfaces.access import SetAccessDTO
from modules.md_database.functions.get_access_by_vehicle_id_if_uncompete import get_access_by_vehicle_id_if_uncomplete
from modules.md_database.functions.get_access_by_identify_if_uncomplete import get_access_by_identify_if_uncomplete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from libs.lb_utils import has_non_none_value

def update_access(id: int, data: SetAccessDTO, idInOut: int = None):
    """
    Aggiunge un record a una tabella specificata dinamicamente con gestione dei conflitti per SQLite.
    """
    with SessionLocal() as session:
        data_to_check = None
        try:
            # Recupera il record specifico in base all'ID
            access = session.query(Access).options(
                    selectinload(Access.vehicle).selectinload(Vehicle.accesses),
                ).filter_by(id=id).one_or_none()
            
            if access is None:
                raise ValueError(f"Record con ID {id} non trovato nella tabella '{Access.__tablename__}'.")

            if access.vehicle and access.vehicle.accesses[-1].id != id and data.number_in_out and data.number_in_out is not None and data.number_in_out != access.number_in_out:
                raise ValueError(f"Puoi modificare il numero di operazioni solo sull'ultimo accesso con la targa '{access.vehicle.plate}'")

            if access.number_in_out is None and data.number_in_out is not None and data.number_in_out != -1:
                raise ValueError(f"Non puoi modificare il numero di operazioni da illimitato a un numero specifico")

            current_model = Subject
            if data.subject.id in [None, -1]:
                add_subject = {
                    "social_reason": data.subject.social_reason if data.subject.social_reason != "" else None,
                    "telephone": data.subject.telephone if data.subject.telephone != "" else None,
                    "cfpiva": data.subject.cfpiva if data.subject.cfpiva != "" else None
                }
                if has_non_none_value(add_subject):
                    data_to_check = data.subject.dict()
                    subject = current_model(**add_subject)
                    session.add(subject)
                    session.flush()
                    access.idSubject = subject.id
                elif data.subject.id == -1:
                    access.idSubject = None
            else:
                access.idSubject = data.subject.id

            current_model = Vector
            if data.vector.id in [None, -1]:
                add_vector = {
                    "social_reason": data.vector.social_reason if data.vector.social_reason != "" else None,
                    "telephone": data.vector.telephone if data.vector.telephone != "" else None,
                    "cfpiva": data.vector.cfpiva if data.vector.cfpiva != "" else None
                }
                if has_non_none_value(add_vector):
                    data_to_check = data.vector.dict()
                    vector = current_model(**add_vector)
                    session.add(vector)
                    session.flush()
                    access.idVector = vector.id
                elif data.vector.id == -1:
                    access.idVector = None
            else:
                access.idVector = data.vector.id

            current_model = Driver
            if data.driver.id in [None, -1]:
                add_driver = {
                    "social_reason": data.driver.social_reason if data.driver.social_reason != "" else None,
                    "telephone": data.driver.telephone if data.driver.telephone != "" else None
                }
                if has_non_none_value(add_driver):
                    data_to_check = data.driver.dict()
                    driver = current_model(**add_driver)
                    session.add(driver)
                    session.flush()
                    access.idDriver = driver.id
                elif data.driver.id == -1:
                    access.idDriver = None
            else:
                access.idDriver = data.driver.id

            # if data.vehicle.id and access.idVehicle and access.idVehicle != data.vehicle.id and len(access.in_out) > 0:
            #     raise ValueError("Non è possibile modificare la targa dopo che è stata effettuata la prima pesata")

            current_reservation_vehicle = access.idVehicle

            current_model = Vehicle
            vehicle = None
            if data.vehicle.id in [None, -1]:
                add_vehicle = {
                    "plate": data.vehicle.plate if data.vehicle.plate != "" else None,
                    "description": data.vehicle.description if data.vehicle.description != "" else None,
                    "tare": data.vehicle.tare if data.vehicle.tare and data.vehicle.tare > 0 else None
                }
                if has_non_none_value(add_vehicle):
                    data_to_check = data.vehicle.dict()
                    vehicle = current_model(**add_vehicle)
                    session.add(vehicle)
                    session.flush()
                    access.idVehicle = vehicle.id
                elif data.vehicle.id == -1:
                    access.idVehicle = None
            else:
                access.idVehicle = data.vehicle.id

            if access.status != AccessStatus.CLOSED and current_reservation_vehicle != data.vehicle.id:
                existing = get_access_by_vehicle_id_if_uncomplete(access.idVehicle)

                if existing and existing["id"] != access.id and existing["idVehicle"]:
                    existing = existing["vehicle"].__dict__
                    plate = existing["plate"]
                    raise ValueError(f"La targa '{plate}' è già assegnata ad un altro accesso ancora aperto")
                elif existing is None and access.idVehicle is not None:
                    existing = get_access_by_identify_if_uncomplete(identify=data.vehicle.plate)
                    if existing and existing["id"] != access.id and existing["idVehicle"]:
                        raise ValueError(f"La targa '{data.vehicle.plate}' è già assegnata come BADGE ad un altro accesso ancora aperto")

            current_model = Material
            material = None
            if idInOut and data.material.id in [None, -1]:
                add_material = {
                    "description": data.material.description if data.material.description != "" else None
                }
                if has_non_none_value(add_material):
                    data_to_check = data.material.dict()
                    material = current_model(**add_material)
                    session.add(material)
                    session.flush()
                    # Find the correct in_out object by id and update its material
                    for in_out in access.in_out:
                        if in_out.id == idInOut:
                            in_out.idMaterial = material.id
                            break
                elif data.material.id == -1:
                    # Find the correct in_out object by id and set material to None
                    for in_out in access.in_out:
                        if in_out.id == idInOut:
                            in_out.idMaterial = None
                            break
            elif idInOut:
                # Find the correct in_out object by id and update its material
                for in_out in access.in_out:
                    if in_out.id == idInOut:
                        in_out.idMaterial = data.material.id
                        break

            # Gestione operator1 per InOut
            if idInOut and data.operator1.id in [None, -1]:
                # Trova l'InOut specifico
                target_in_out = None
                for in_out in access.in_out:
                    if in_out.id == idInOut:
                        target_in_out = in_out
                        break
                
                if target_in_out and target_in_out.idWeight1:
                    add_operator1 = {
                        "description": data.operator1.description if data.operator1.description != "" else None
                    }
                    if has_non_none_value(add_operator1):
                        current_model = Operator
                        data_to_check = data.operator1.dict()
                        operator1 = current_model(**add_operator1)
                        session.add(operator1)
                        session.flush()
                        # Aggiorna l'operatore della prima pesata
                        weight1 = session.query(Weighing).filter_by(id=target_in_out.idWeight1).first()
                        if weight1:
                            weight1.idOperator = operator1.id
                    elif data.operator1.id == -1:
                        # Rimuovi l'operatore dalla prima pesata
                        weight1 = session.query(Weighing).filter_by(id=target_in_out.idWeight1).first()
                        if weight1:
                            weight1.idOperator = None
            elif idInOut:
                # Assegna operatore esistente alla prima pesata
                for in_out in access.in_out:
                    if in_out.id == idInOut:
                        if in_out.idWeight1:
                            weight1 = session.query(Weighing).filter_by(id=in_out.idWeight1).first()
                            if weight1:
                                weight1.idOperator = data.operator1.id
                        break

            # Gestione operator2 per InOut
            if idInOut and data.operator2.id in [None, -1]:
                # Trova l'InOut specifico
                target_in_out = None
                for in_out in access.in_out:
                    if in_out.id == idInOut:
                        target_in_out = in_out
                        break
                
                if target_in_out and target_in_out.idWeight2:
                    add_operator2 = {
                        "description": data.operator2.description if data.operator2.description != "" else None
                    }
                    if has_non_none_value(add_operator2):
                        current_model = Operator
                        data_to_check = data.operator2.dict()
                        operator2 = current_model(**add_operator2)
                        session.add(operator2)
                        session.flush()
                        # Aggiorna l'operatore della seconda pesata
                        weight2 = session.query(Weighing).filter_by(id=target_in_out.idWeight2).first()
                        if weight2:
                            weight2.idOperator = operator2.id
                    elif data.operator2.id == -1:
                        # Rimuovi l'operatore dalla seconda pesata
                        weight2 = session.query(Weighing).filter_by(id=target_in_out.idWeight2).first()
                        if weight2:
                            weight2.idOperator = None
            elif idInOut:
                # Assegna operatore esistente alla seconda pesata
                for in_out in access.in_out:
                    if in_out.id == idInOut:
                        if in_out.idWeight2:
                            weight2 = session.query(Weighing).filter_by(id=in_out.idWeight2).first()
                            if weight2:
                                weight2.idOperator = data.operator2.id
                        break

            if data.typeSubject:
                access.typeSubject = TypeSubjectEnum[data.typeSubject]

            if data.number_in_out is not None:
                if data.number_in_out != -1:
                    if len(access.in_out) > data.number_in_out:
                        raise ValueError("Non puoi assegnare un numero di pesate inferiore a quelle già effettuate")
                access.number_in_out = data.number_in_out if data.number_in_out != -1 else None
                if len(access.in_out) > 0:
                    if data.number_in_out == -1:
                        access.status = AccessStatus.ENTERED
                    else:
                        access.status = AccessStatus.CLOSED if len(access.in_out) == access.number_in_out and access.in_out[-1].idWeight2 else AccessStatus.ENTERED
                else:
                    access.status = AccessStatus.WAITING

            if data.note is not None:
                access.note = data.note if data.note != "" else None

            if data.document_reference is not None:
                access.document_reference = data.document_reference if data.document_reference != "" else None

            badge = data.badge
            if badge is not None:
                # Controllo per duplicati badge (escludendo la prenotazione corrente)
                if badge != "":
                    existing_badge = session.query(Access).filter(
                        Access.badge == badge,
                        Access.id != id  # Escludi la prenotazione corrente
                    ).first()
                    
                    if existing_badge:
                        raise ValueError(f"Il badge '{badge}' è già assegnato ad un altro accesso")
                    else:
                        existing_badge = get_access_by_identify_if_uncomplete(identify=badge)
                        if existing_badge and existing_badge["id"] != id:
                            raise ValueError(f"Il badge '{badge}' è già assegnato come TARGA ad un altro accesso ancora aperto")
                
                access.badge = badge if badge != "" else None

            session.commit()

            session.refresh(access)

            return access.__dict__
        except IntegrityError as e:
            session.rollback()
            error_message = str(e)
            
            # Lista per tenere traccia di tutti i conflitti trovati
            conflicts = []
            
            # Cerchiamo tutti i vincoli di unicità violati
            if "UNIQUE constraint failed:" in error_message:
                # Estrazione della parte dopo "UNIQUE constraint failed:"
                table_part = error_message.split("UNIQUE constraint failed:")[1].strip()
                # Può contenere vincoli multipli separati da virgole
                constraint_parts = table_part.split(',')

                for part in constraint_parts:
                    part = part.strip()
                    # Verifichiamo se contiene un punto che separa nome tabella e colonna
                    if '.' in part:
                        table_column = part.split('.')
                        # Assicuriamoci che ci siano abbastanza elementi dopo lo split
                        if len(table_column) >= 2:
                            column_name = table_column[1].strip()
                            if column_name in data_to_check:
                                conflicts.append(f"{column_name}: {data_to_check[column_name]}")
            
            # Se non siamo riusciti a estrarre i conflitti con il metodo precedente
            # proviamo con un approccio alternativo
            if not conflicts:
                unique_columns = [column.name for column in current_model.__table__.columns if column.unique]
                for column in unique_columns:
                    if column in data_to_check:
                        # Verifichiamo se questo valore esiste già nel database
                        existing = session.query(current_model).filter(getattr(current_model, column) == data_to_check[column]).first()
                        if existing:
                            conflicts.append(f"{column}: {data_to_check[column]}")
            
            if conflicts:
                conflict_details = ', '.join(conflicts)
                raise HTTPException(
                    status_code=400,
                    detail=f"Conflitto sui vincoli di unicità. I seguenti valori sono duplicati in '{current_model.__tablename__}': {conflict_details}"
                )
            else:
                # Fallback se non riusciamo a determinare i conflitti specifici
                raise HTTPException(
                    status_code=400,
                    detail=f"Conflitto su uno o più vincoli di unicità. Non puoi duplicare questo record."
                )
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()