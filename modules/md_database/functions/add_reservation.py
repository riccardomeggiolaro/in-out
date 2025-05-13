from modules.md_database.md_database import SessionLocal, Subject, Vector, Driver, Vehicle, Reservation, ReservationStatus, TypeSubjectEnum
from modules.md_database.interfaces.reservation import AddReservationDTO
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from libs.lb_utils import has_non_none_value

def add_reservation(data: AddReservationDTO):
    """
    Aggiunge un record a una tabella specificata dinamicamente con gestione dei conflitti per SQLite.
    """
    with SessionLocal() as session:
        try:
            add_reservation = {
                "typeSubject": TypeSubjectEnum.CUSTOMER,
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
                    subject = current_model(**add_subject)
                    session.add(subject)
                    add_reservation["idSubject"] = subject["id"]

            current_model = Vector
            if not data.vector.id:
                add_vector = {
                    "social_reason": data.vector.social_reason if data.vector.social_reason != "" else None,
                    "telephone": data.vector.telephone if data.vector.telephone != "" else None,
                    "cfpiva": data.vector.cfpiva if data.vector.cfpiva != "" else None
                }
                if has_non_none_value(add_vector):
                    vector = current_model(**add_vector)
                    session.add(vector)
                    add_reservation["idVector"] = vector["id"]

            current_model = Driver
            if not data.driver.id:
                add_driver = {
                    "social_reason": data.driver.social_reason if data.driver.social_reason != "" else None,
                    "telephone": data.driver.telephone if data.driver.telephone != "" else None
                }
                if has_non_none_value(add_driver):
                    driver = current_model(**add_driver)
                    session.add(driver)
                    add_reservation["idDriver"] = driver["id"]
            
            current_model = Vehicle
            if not data.vehicle.id:
                add_vehicle = {
                    "plate": data.vehicle.plate if data.vehicle.plate != "" else None,
                    "description": data.vehicle.description if data.vehicle.description != "" else None
                }
                if has_non_none_value(add_vehicle):
                    vehicle = current_model(**add_vehicle)
                    session.add(vehicle)
                    add_reservation["idVehicle"] = vehicle["id"]

            current_model = Reservation
            reservation = current_model(**add_reservation)
            session.add(reservation)

            session.commit()

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
                
                for part in constraint_parts:
                    part = part.strip()
                    # Verifichiamo se contiene un punto che separa nome tabella e colonna
                    if '.' in part:
                        table_column = part.split('.')
                        # Assicuriamoci che ci siano abbastanza elementi dopo lo split
                        if len(table_column) >= 2:
                            column_name = table_column[1].strip()
                            if column_name in data:
                                conflicts.append(f"{column_name}: {data[column_name]}")
            
            # Se non siamo riusciti a estrarre i conflitti con il metodo precedente
            # proviamo con un approccio alternativo
            if not conflicts:
                unique_columns = [column.name for column in current_model.__table__.columns if column.unique]
                for column in unique_columns:
                    if column in data:
                        # Verifichiamo se questo valore esiste già nel database
                        existing = session.query(current_model).filter(getattr(current_model, column) == data[column]).first()
                        if existing:
                            conflicts.append(f"{column}: {data[column]}")
            
            if conflicts:
                conflict_details = ', '.join(conflicts)
                raise HTTPException(
                    status_code=400,
                    detail=f"Conflitto sui vincoli di unicità. I seguenti valori sono duplicati: {conflict_details}"
                )
            else:
                # Fallback se non riusciamo a determinare i conflitti specifici
                raise HTTPException(
                    status_code=400,
                    detail=f"Conflitto su uno o più vincoli di unicità. Non puoi duplicare questo record."
                )
        except Exception as e:
            session.rollback()
        finally:
            session.close()