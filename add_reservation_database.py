import sqlite3

cursor = sqlite3.connect('database.db')

cursor.execute("INSERT INTO reservation (idSubject, idVehicle, number_weighings, note, status, date_created) VALUES (1, 1, 1, 'Ciaone di cuore', 'WAITING', '2025-04-01 17:34:50.563892')")

cursor.commit()

cursor.close()