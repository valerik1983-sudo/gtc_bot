# add_column_consult.py
import sqlite3

def add_column():
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE consult_requests ADD COLUMN admin_notified INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Колонка admin_notified добавлена в таблицу consult_requests")
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Возможно, колонка уже существует")
    conn.close()

if __name__ == "__main__":
    add_column()