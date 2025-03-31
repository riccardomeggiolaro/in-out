import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

cursor.execute("DELETE FROM reservation")

conn.commit()

conn.close()