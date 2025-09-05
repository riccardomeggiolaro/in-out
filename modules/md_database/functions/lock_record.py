from sqlalchemy.exc import IntegrityError
from modules.md_database.md_database import Access, InOut, LockRecord, SessionLocal, LockRecordType
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

def lock_record(table_name, idRecord, type, websocket_identifier, user_id, weigher_name):
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

            # Controllo speciale per tabelle diverse da access
            if table_name != "access":
                # --- INIZIO BLOCCO PER MATERIAL ---
                if table_name == "material" and type != "SELECT":
                    # Trova tutte le access bloccate
                    locked_res_ids = session.query(LockRecord.idRecord).filter(
                        LockRecord.table_name == "access",
                        LockRecord.type.in_([
                            LockRecordType.UPDATE, LockRecordType.DELETE, 
                            LockRecordType.CALL, LockRecordType.CANCEL_CALL,
                            LockRecordType.SELECT
                        ])
                    ).subquery()
                    # Cerca se esiste almeno una access bloccata che ha un InOut con quel materiale
                    blocked_res_with_material = session.query(Access).join(Access.in_out).filter(
                        Access.id.in_(locked_res_ids),
                        InOut.idMaterial == idRecord
                    ).first()
                    if blocked_res_with_material:
                        # Trova il lock record della access bloccata
                        lock = session.query(LockRecord).options(joinedload(LockRecord.user)).filter(
                            LockRecord.table_name == "access",
                            LockRecord.idRecord == blocked_res_with_material.id
                        ).first()
                        return False, lock, "material"
                # --- FINE BLOCCO PER MATERIAL ---

                # Controlla se questo record è associato a prenotazioni bloccate
                # Questa query cerca prenotazioni associate al record corrente
                # che sono anche bloccate nella tabella LockRecord
                
                # Prima, identifichiamo la colonna chiave estera nella tabella Access
                # che fa riferimento alla tabella specificata
                foreign_key_column = None
                
                # Mappa delle chiavi esterne che collegano Access con altre tabelle
                foreign_key_map = {
                    "subject": Access.idSubject,
                    "vector": Access.idVector,
                    "driver": Access.idDriver,
                    "vehicle": Access.idVehicle
                }
                
                if table_name in foreign_key_map and type != "SELECT":
                    foreign_key_column = foreign_key_map[table_name]
                    
                    # Cerca prenotazioni collegate al record corrente
                    reservations_subquery = session.query(Access.id).filter(
                        foreign_key_column == idRecord
                    ).subquery()
                    
                    # Cerca blocchi sulle prenotazioni trovate
                    reservation_locks = session.query(LockRecord).filter(
                        and_(
                            LockRecord.table_name == "access",
                            LockRecord.idRecord.in_(reservations_subquery),
                            LockRecord.type.in_([LockRecordType.UPDATE, LockRecordType.DELETE, 
                                               LockRecordType.CALL, LockRecordType.CANCEL_CALL,
                                               LockRecordType.SELECT])
                        )
                    ).first()
                    
                    if reservation_locks:
                        # Se troviamo un blocco su una prenotazione associata, carichiamo anche l'utente
                        locked_reservation = session.query(LockRecord).options(
                            joinedload(LockRecord.user)
                        ).filter(LockRecord.id == reservation_locks.id).first()
                        
                        # Restituisci False e il blocco trovato
                        return False, locked_reservation, None
                        
           # Controllo speciale per le prenotazioni
            elif table_name == "access":
                # Prima otteniamo i dati della prenotazione per conoscere le entità associate
                reservation_data = session.query(Access).filter(Access.id == idRecord).first()
                
                if reservation_data:
                    # Mappa delle entità associate con i loro ID
                    associated_entities = {
                        "subject": reservation_data.idSubject,
                        "vector": reservation_data.idVector,
                        "driver": reservation_data.idDriver,
                        "vehicle": reservation_data.idVehicle
                    }
                    
                    # Controlliamo se c'è un blocco su qualsiasi entità associata
                    for entity_name, entity_id in associated_entities.items():
                        if entity_id:  # Verifica solo se l'ID esiste
                            entity_lock = session.query(LockRecord).filter(
                                LockRecord.table_name == entity_name,
                                LockRecord.idRecord == entity_id,
                                LockRecord.type.in_([LockRecordType.UPDATE, LockRecordType.DELETE])
                            ).first()
                            
                            if entity_lock:
                                # Se troviamo un blocco, carichiamo i dettagli dell'utente
                                locked_entity = session.query(LockRecord).options(
                                    joinedload(LockRecord.user)
                                ).filter(LockRecord.id == entity_lock.id).first()
                                
                                # Restituisci False e il blocco trovato
                                return False, locked_entity, entity_name

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
                # Carica anche l'utente associato
                existing = session.query(LockRecord).options(joinedload(LockRecord.user)).filter(
                    LockRecord.id == existing.id
                ).first()
                return False, existing, None

            # Prova a creare il blocco
            nuovo_record = LockRecord(
                table_name=table_name,
                idRecord=idRecord,
                type=type,
                websocket_identifier=websocket_identifier,
                user_id=user_id,
                weigher_name=weigher_name
            )
            session.add(nuovo_record)
            session.commit()
            session.refresh(nuovo_record)
            return True, nuovo_record, None
        except IntegrityError:
            # Questo errore si verificherà solo quando si tenta di inserire un record duplicato
            # con type="UPDATE" o "DELETE", grazie all'indice parziale
            session.rollback()
            
            # Recupera il record esistente che causa il conflitto e carica l'utente associato
            existing_record = session.query(LockRecord).options(joinedload(LockRecord.user)).filter(
                LockRecord.table_name == table_name,
                LockRecord.idRecord == idRecord,
                LockRecord.type.in_([LockRecordType.UPDATE, LockRecordType.DELETE])
            ).first()

            return False, existing_record, None
        except Exception as e:
            session.rollback()
            return False, None, None