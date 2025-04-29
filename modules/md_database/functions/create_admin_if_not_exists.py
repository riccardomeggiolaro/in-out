from modules.md_database.md_database import SessionLocal, User
from modules.md_database.interfaces.user import hash_password

# Funzione per creare l'utente admin se non esiste
def create_admin_user_if_not_exists(username, password):
    with SessionLocal() as db_session:
        # Controlla se l'utente admin esiste già
        admin_user = db_session.query(User).filter(User.username == "admin").first()
    
        if admin_user is None:
            admin_user = User(
                username=username,
                password=hash_password(password),  # Sostituisci con una password sicura
                level=3,  # Imposta il livello appropriato, ad esempio 1 per admin
                description="Administrator"
            )
            db_session.add(admin_user)
            db_session.commit()