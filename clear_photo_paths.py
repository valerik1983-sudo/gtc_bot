# clear_photo_paths.py
from database import get_connection

def clear_photos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET photo_path = NULL")
    conn.commit()
    print("✅ Все photo_path очищены")
    conn.close()

if __name__ == "__main__":
    clear_photos()