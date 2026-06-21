# check_db_structure.py
from database import get_connection

def check_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем структуру таблицы products
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    
    print("📋 Структура таблицы products:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Проверяем, есть ли поле photo_path
    has_photo = any(col[1] == 'photo_path' for col in columns)
    print(f"\n📷 Поле photo_path существует: {'✅ ДА' if has_photo else '❌ НЕТ'}")
    
    # Проверяем несколько товаров
    cursor.execute("SELECT id, name, photo_path FROM products LIMIT 5")
    products = cursor.fetchall()
    
    print("\n📦 Примеры товаров:")
    for p in products:
        print(f"   ID: {p[0]}, Name: {p[1]}, photo_path: {p[2] if p[2] else '❌ пусто'}")
    
    conn.close()

if __name__ == "__main__":
    check_db()