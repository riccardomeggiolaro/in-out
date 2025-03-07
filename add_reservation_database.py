import sqlite3

cursor = sqlite3.connect('database.db')

cursor.execute("INSERT INTO reservation (idCustomer, idSupplier, idVehicle, idMaterial, number_weighings, note) VALUES (1, 1, 1, 1, 2, 'Esempio di prenotazione')")

cursor.commit()

cursor.close()