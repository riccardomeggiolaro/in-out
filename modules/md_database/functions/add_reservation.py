from modules.md_database.md_database import SessionLocal, Subject, Vector, Driver, Vehicle, Reservation, ReservationStatus, TypeSubjectEnum
from modules.md_database.interfaces.reservation import AddReservationDTO
from modules.md_database.functions.get_reservation_by_vehicle_id_if_uncompete import get_reservation_by_vehicle_id_if_incomplete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from libs.lb_utils import has_non_none_value
import libs.lb_log as lb_log

def add_reservation(data: AddReservationDTO):
    """
    Aggiunge un record a una tabella specificata dinamicamente con gestione dei conflitti per SQLite.
    """
    with SessionLocal() as session:
        data_to_check = None
        try:
            add_reservation = {
                "typeSubject": TypeSubjectEnum[data.typeSubject],
                "idSubject": data.subject.id,
                "idVector": data.vector.id,
                "idDriver": data.driver.id,
                "idVehicle": data.vehicle.id,
                "number_weighings": data.number_weighings,
                "note": data.note,
                "status": ReservationStatus.WAITING,
                "document_reference": data.document_reference
            }

            current_model = Subject
            if not data.subject.id:
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
                    add_reservation["idSubject"] = subject.id

            current_model = Vector
            if not data.vector.id:
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
                    add_reservation["idVector"] = vector.id

            current_model = Driver
            if not data.driver.id:
                add_driver = {
                    "social_reason": data.driver.social_reason if data.driver.social_reason != "" else None,
                    "telephone": data.driver.telephone if data.driver.telephone != "" else None
                }
                if has_non_none_value(add_driver):
                    data_to_check = data.driver.dict()
                    driver = current_model(**add_driver)
                    session.add(driver)
                    session.flush()
                    add_reservation["idDriver"] = driver.id
            
            current_model = Vehicle
            vehicle = None
            if not data.vehicle.id:
                add_vehicle = {
                    "plate": data.vehicle.plate if data.vehicle.plate != "" else None,
                    "description": data.vehicle.description if data.vehicle.description != "" else None
                }
                if has_non_none_value(add_vehicle):
                    data_to_check = data.vehicle.dict()
                    vehicle = current_model(**add_vehicle)
                    session.add(vehicle)
                    session.flush()
                    add_reservation["idVehicle"] = vehicle.id

            existing = get_reservation_by_vehicle_id_if_incomplete(add_reservation["idVehicle"])

            if existing:
                existing = existing["vehicle"].__dict__
                plate = existing["plate"]
                raise Exception(f"E' presente una prenotazione con la targa '{plate}' ancora da chiudere")

            current_model = Reservation
            data_to_check = data.dict()
            reservation = current_model(**add_reservation)
            session.add(reservation)

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
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()