from modules.md_database.md_database import SessionLocal, Subject, Vector, Driver, Vehicle, Material, Reservation, ReservationStatus, TypeSubjectEnum
from modules.md_database.interfaces.reservation import SetReservationDTO
from modules.md_database.functions.get_reservation_by_vehicle_id_if_uncompete import get_reservation_by_vehicle_id_if_incomplete
from modules.md_database.functions.update_data import update_data
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from libs.lb_utils import has_non_none_value
import libs.lb_log as lb_log

def update_reservation(id: int, data: SetReservationDTO, idInOut: int = None):
    """
    Aggiunge un record a una tabella specificata dinamicamente con gestione dei conflitti per SQLite.
    """
    with SessionLocal() as session:
        data_to_check = None
        try:
            # Recupera il record specifico in base all'ID
            reservation = session.query(Reservation).filter_by(id=id).one_or_none()
            
            if reservation is None:
                raise ValueError(f"Record con ID {id} non trovato nella tabella '{Reservation.__tablename__}'.")

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
                    reservation.idSubject = subject.id
                elif data.subject.id == -1:
                    reservation.idSubject = None
            else:
                reservation.idSubject = data.subject.id

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
                    reservation.idVector = vector.id
                elif data.vector.id == -1:
                    reservation.idVector = None
            else:
                reservation.idVector = data.vector.id

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
                    reservation.idDriver = driver.id
                elif data.driver.id == -1:
                    reservation.idDriver = None
            else:
                reservation.idDriver = data.driver.id

            # if data.vehicle.id and reservation.idVehicle and reservation.idVehicle != data.vehicle.id and len(reservation.in_out) > 0:
            #     raise ValueError("Non è possibile modificare la targa dopo che è stata effettuata la prima pesata")

            current_model = Vehicle
            vehicle = None
            if data.vehicle.id in [None, -1]:
                add_vehicle = {
                    "plate": data.vehicle.plate if data.vehicle.plate != "" else None,
                    "description": data.vehicle.description if data.vehicle.description != "" else None,
                    "tag": data.vehicle.tag if data.vehicle.tag != "" else None
                }
                if has_non_none_value(add_vehicle):
                    data_to_check = data.vehicle.dict()
                    vehicle = current_model(**add_vehicle)
                    session.add(vehicle)
                    session.flush()
                    reservation.idVehicle = vehicle.id
                elif data.vehicle.id == -1:
                    reservation.idVehicle = None
            else:
                reservation.idVehicle = data.vehicle.id

            existing = get_reservation_by_vehicle_id_if_incomplete(reservation.idVehicle)

            if existing and existing["id"] != reservation.id and existing["idVehicle"]:
                existing = existing["vehicle"].__dict__
                plate = existing["plate"]
                raise ValueError(f"E' presente una prenotazione con il veicolo '{plate}' ancora da chiudere")

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
                    for in_out in reservation.in_out:
                        if in_out.id == idInOut:
                            in_out.idMaterial = material.id
                            break
                elif data.material.id == -1:
                    # Find the correct in_out object by id and set material to None
                    for in_out in reservation.in_out:
                        if in_out.id == idInOut:
                            in_out.idMaterial = None
                            break
            elif idInOut:
                # Find the correct in_out object by id and update its material
                for in_out in reservation.in_out:
                    if in_out.id == idInOut:
                        in_out.idMaterial = data.material.id
                        break

            if data.typeSubject:
                reservation.typeSubject = TypeSubjectEnum[data.typeSubject]

            if data.number_in_out:
                if len(reservation.in_out) > data.number_in_out:
                    raise ValueError("Non puoi assegnare un numero di pesate inferiore a quelle già effettuate")
                reservation.number_in_out = data.number_in_out
                if len(reservation.in_out) > 0:
                    reservation.status = ReservationStatus.CLOSED if len(reservation.in_out) == reservation.number_in_out and reservation.in_out[-1].idWeight2 else ReservationStatus.ENTERED
                else:
                    reservation.status = ReservationStatus.WAITING

            if data.note is not None:
                reservation.note = data.note if data.note != "" else None

            if data.document_reference is not None:
                reservation.document_reference = data.document_reference if data.document_reference != "" else None

            session.commit()

            session.refresh(reservation)

            return reservation.__dict__
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

                lb_log.warning(constraint_parts)
                
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
                        lb_log.warning(column)
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
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()