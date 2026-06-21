# fix_office_cities.py
from database import get_connection

def fix_office_cities():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем существующие таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("📋 Таблицы в БД:", [t[0] for t in tables])
    
    # Проверяем структуру office_cities
    cursor.execute("PRAGMA table_info(office_cities)")
    columns = cursor.fetchall()
    print(f"\n📋 Структура office_cities: {[(c[1], c[2]) for c in columns]}")
    
    # Если нет колонки city, пересоздаём таблицу
    has_city = any(c[1] == 'city' for c in columns)
    
    if not has_city:
        print("\n🔧 Таблица office_cities имеет неверную структуру. Пересоздаём...")
        
        # Сохраняем старые данные если есть
        cursor.execute("SELECT * FROM office_cities")
        old_data = cursor.fetchall()
        
        # Удаляем старую таблицу
        cursor.execute("DROP TABLE IF EXISTS office_cities")
        
        # Создаём новую с правильной структурой
        cursor.execute("""
            CREATE TABLE office_cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT UNIQUE NOT NULL
            )
        """)
        
        # Восстанавливаем данные
        for row in old_data:
            if len(row) > 1:  # Если есть второй столбец
                cursor.execute("INSERT OR IGNORE INTO office_cities (city) VALUES (?)", (row[1],))
            elif len(row) > 0:
                cursor.execute("INSERT OR IGNORE INTO office_cities (city) VALUES (?)", (row[0],))
        
        conn.commit()
        print("✅ Таблица office_cities пересоздана")
    
    # Добавляем тестовые города если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM office_cities")
    count = cursor.fetchone()[0]
    
    if count == 0:
        default_cities = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск"]
        for city in default_cities:
            cursor.execute("INSERT OR IGNORE INTO office_cities (city) VALUES (?)", (city,))
        conn.commit()
        print(f"✅ Добавлены города: {default_cities}")
    
    # Проверяем результат
    cursor.execute("SELECT * FROM office_cities")
    cities = cursor.fetchall()
    print(f"\n📋 Города в БД: {[c[1] for c in cities]}")
    
    conn.close()

if __name__ == "__main__":
    fix_office_cities()