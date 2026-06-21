# check_user.py
from database import get_user, get_sponsor, get_connection
import sqlite3

def check_user_data(telegram_id):
    """Проверка данных пользователя"""
    print(f"\n🔍 Проверка пользователя {telegram_id}...")
    
    # Получаем пользователя через функцию из database.py
    user = get_user(telegram_id)
    if user:
        print(f"✅ Пользователь найден:")
        print(f"   - ID: {user['telegram_id']}")
        print(f"   - ФИО: {user['fio']}")
        print(f"   - Статус: {user['status']}")
        print(f"   - Телефон: {user.get('phone', 'Не указан')}")
    else:
        print(f"❌ Пользователь НЕ зарегистрирован!")
        return
    
    # Получаем наставника
    sponsor = get_sponsor(telegram_id)
    if sponsor and sponsor['sponsor_id']:
        print(f"\n👤 Наставник найден:")
        print(f"   - Sponsor ID: {sponsor['sponsor_id']}")
        
        # Получаем данные наставника
        sponsor_user = get_user(int(sponsor['sponsor_id']))
        if sponsor_user:
            print(f"   - ФИО наставника: {sponsor_user['fio']}")
            print(f"   - Telegram ID наставника: {sponsor_user['telegram_id']}")
        else:
            print(f"   ⚠️ Наставник с ID {sponsor['sponsor_id']} не найден в таблице!")
    else:
        print(f"\n❌ Наставник НЕ найден!")
    
    # Проверяем реальную структуру БД
    print(f"\n📋 Структура базы данных:")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"   Таблицы в БД: {[t[0] for t in tables]}")
    
    # Для каждой таблицы показываем первые 5 записей
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print(f"\n   📊 Таблица '{table_name}': {len(rows)} записей")
                # Получаем названия колонок
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"      Колонки: {columns}")
                for row in rows:
                    print(f"      {row}")
        except Exception as e:
            print(f"   Ошибка при чтении {table_name}: {e}")
    
    conn.close()

if __name__ == "__main__":
    # Замените на свой Telegram ID
    YOUR_TELEGRAM_ID = 7878181865  # Ваш ID
    check_user_data(YOUR_TELEGRAM_ID)