import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

cursor.execute("DELETE FROM lock_record")

conn.commit()

conn.close()