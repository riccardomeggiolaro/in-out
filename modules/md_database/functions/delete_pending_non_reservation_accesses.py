from modules.md_database.md_database import SessionLocal, Access, AccessStatus, TypeAccess, InOut
import libs.lb_log as lb_log

def delete_pending_non_reservation_accesses():
    """
    Elimina tutti gli accessi pendenti (status WAITING) che non sono prenotazioni (type != RESERVATION)
    e che non hanno pesate associate (in_out).
    Viene eseguita automaticamente dopo la mezzanotte.

    Returns:
        list: Lista degli ID degli accessi eliminati.
    """
    session = SessionLocal()
    try:
        # Trova accessi in stato WAITING che non sono RESERVATION
        accesses_to_delete = session.query(Access).filter(
            Access.status == AccessStatus.WAITING,
            Access.type != TypeAccess.RESERVATION
        ).all()

        deleted_ids = []
        for access in accesses_to_delete:
            # Verifica che l'accesso non abbia pesate associate
            in_out_count = session.query(InOut).filter(InOut.idAccess == access.id).count()
            if in_out_count == 0:
                deleted_ids.append(access.id)
                session.delete(access)

        session.commit()

        if deleted_ids:
            lb_log.info(f"Pulizia mezzanotte: eliminati {len(deleted_ids)} accessi pendenti non prenotati (IDs: {deleted_ids})")
        else:
            lb_log.info("Pulizia mezzanotte: nessun accesso pendente non prenotato da eliminare")

        return deleted_ids

    except Exception as e:
        session.rollback()
        lb_log.error(f"Errore durante la pulizia degli accessi pendenti: {e}")
        raise e
    finally:
        session.close()
