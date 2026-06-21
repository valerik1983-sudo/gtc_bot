# check_programs.py
from database import get_connection

def check_programs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, is_active FROM programs")
    programs = cursor.fetchall()
    for p in programs:
        print(f"ID: {p['id']}, Name: {p['name']}, is_active: {p['is_active']}")
    conn.close()

if __name__ == "__main__":
    check_programs()