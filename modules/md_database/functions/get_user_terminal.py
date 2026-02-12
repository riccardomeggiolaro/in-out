from modules.md_database.md_database import SessionLocal, User

# Funzione per creare l'utente admin se non esiste
def get_user_terminal_and_create_if_not_exists():
    with SessionLocal() as db_session:
        # Controlla se l'utente admin esiste già
        terminal_user = db_session.query(User).filter(User.username == "terminal").first()
    
        if terminal_user is None:
            terminal_user = User(
                username="terminal",
                password=None,
                level=0,
                description="Terminal"
            )
            db_session.add(terminal_user)
            db_session.commit()
        
        return terminal_user