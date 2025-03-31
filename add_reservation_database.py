import sqlite3

cursor = sqlite3.connect('database.db')

cursor.execute("INSERT INTO reservation (idSubject, idVehicle, number_weighings, note) VALUES (1, 1, 1, 'Ciaone di cuore')")

cursor.commit()

cursor.close()