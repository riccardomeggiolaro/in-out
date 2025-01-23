import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

cursor.execute("DELETE FROM weighing")


cursor.execute("DELETE FROM image_captured")


cursor.execute("DELETE FROM customer")


cursor.execute("DELETE FROM material")


cursor.execute("DELETE FROM supplier")


cursor.execute("DELETE FROM vehicle")

conn.commit()

conn.close()