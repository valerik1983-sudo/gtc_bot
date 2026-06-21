from database import get_connection

def update_orders_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем и добавляем колонки
    cursor.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "status" not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'new'")
        print("✅ Добавлена колонка status")
    
    if "tracking_number" not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN tracking_number TEXT")
        print("✅ Добавлена колонка tracking_number")
    
    if "updated_at" not in columns:
        # SQLite не поддерживает DEFAULT CURRENT_TIMESTAMP при ALTER TABLE
        cursor.execute("ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP")
        print("✅ Добавлена колонка updated_at (без DEFAULT)")
    
    conn.commit()
    conn.close()
    print("✅ Таблица orders обновлена")

if __name__ == "__main__":
    update_orders_table()