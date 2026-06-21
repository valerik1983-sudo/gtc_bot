# check_consult_db.py
import sqlite3

conn = sqlite3.connect("consultations.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM consult_requests")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()