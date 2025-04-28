from sqlalchemy.exc import IntegrityError
from modules.md_database.md_database import LockRecord, SessionLocal, LockRecordType

def lock_record(table_name, idRecord, type, websocket_identifier, user_id):
    """
    Prova a bloccare un record.
    Il database applicherà automaticamente il vincolo di unicità solo quando type è "UPDATE" o "DELETE".
    
    Restituisce:
    - (True, record) se il blocco ha successo
    - (False, existing_record) se il record è già bloccato (solo per UPDATE/DELETE)
    """
    with SessionLocal() as session:
        try:
            existing = None

            if type == "SELECT":
                existing = session.query(LockRecord).filter(
                    LockRecord.table_name == table_name,
                    LockRecord.idRecord == idRecord,
                    LockRecord.type.in_([LockRecordType.UPDATE, LockRecordType.DELETE])
                ).first()
            elif type == "CALL":
                existing = session.query(LockRecord).filter(
                    LockRecord.table_name == table_name,
                    LockRecord.idRecord == idRecord,
                    LockRecord.type.in_([LockRecordType.UPDATE, LockRecordType.DELETE, LockRecordType.CALL, LockRecordType.CANCEL_CALL])
                ).first()
            elif type == "CANCEL_CALL":
                existing = session.query(LockRecord).filter(
                    LockRecord.table_name == table_name,
                    LockRecord.idRecord == idRecord,
                    LockRecord.type.in_([LockRecordType.UPDATE, LockRecordType.DELETE, LockRecordType.CALL, LockRecordType.CANCEL_CALL])
                ).first()
            elif type in ["UPDATE", "DELETE"]:
                existing = session.query(LockRecord).filter(
                    LockRecord.table_name == table_name,
                    LockRecord.idRecord == idRecord
                ).first()                
                
            if existing:
                return False, existing

            # Prova a creare il blocco
            nuovo_record = LockRecord(
                table_name=table_name,
                idRecord=idRecord,
                type=type,
                websocket_identifier=websocket_identifier,
                user_id=user_id
            )
            session.add(nuovo_record)
            session.commit()
            session.refresh(nuovo_record)
            return True, nuovo_record
        except IntegrityError:
            # Questo errore si verificherà solo quando si tenta di inserire un record duplicato
            # con type="UPDATE" o type="DELETE", grazie all'indice parziale
            session.rollback()
            
            # Recupera il record esistente che causa il conflitto
            existing_record = session.query(LockRecord).filter(
                LockRecord.table_name == table_name,
                LockRecord.idRecord == idRecord,
                LockRecord.type.in_([LockRecordType.UPDATE, LockRecordType.DELETE])
            ).first()

            return False, existing_record
        except Exception as e:
            session.rollback()
            return False, None