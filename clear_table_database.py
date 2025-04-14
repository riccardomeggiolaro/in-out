import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

cursor.execute("""
            INSERT INTO weighing_picture (path_name, idWeighing)
            VALUES ('/2025/04/00000-001976_P1.png', 1);
               """)

conn.commit()

conn.close()