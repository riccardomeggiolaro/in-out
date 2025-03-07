import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

cursor.execute("DELETE FROM weighing")

cursor.execute("DELETE FROM social_reason")

cursor.execute("DELETE FROM vehicle")

cursor.execute("DELETE FROM material")

cursor.execute("DELETE FROM reservation")

conn.commit()

conn.close()