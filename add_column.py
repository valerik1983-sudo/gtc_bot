# add_column.py
from database import get_connection

def add_column():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN admin_notified INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Колонка admin_notified добавлена в таблицу orders")
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Возможно, колонка уже существует")
    conn.close()

if __name__ == "__main__":
    add_column()