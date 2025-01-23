import sqlite3

# Connessione al database (se non esiste, verrà creato)
conn = sqlite3.connect('database.db')

# Creazione di un cursore
cursor = conn.cursor()

# Esegui la query per eliminare tutti i record dalla tabella
cursor.execute("DELETE FROM weighing")

# Commit per applicare le modifiche
conn.commit()

# Chiudere la connessione
conn.close()