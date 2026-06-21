# check_photos.py
from database import get_connection

def check():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, photo_path FROM products")
    for row in cursor.fetchall():
        print(f"ID: {row['id']}, Name: {row['name']}, photo: {row['photo_path'][:50] if row['photo_path'] else 'NULL'}")
    conn.close()

if __name__ == "__main__":
    check()