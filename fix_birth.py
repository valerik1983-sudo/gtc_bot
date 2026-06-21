import sqlite3

DB_NAME = "crm.db"

def fix_birth():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # ⬇️ ЗАМЕНИТЕ 733275095 на реальный Telegram ID пользователя
    # ⬇️ ЗАМЕНИТЕ '30.01.1959' на нужную дату в формате ДД.ММ.ГГГГ
    cursor.execute(
        "UPDATE users SET birth_date = ? WHERE telegram_id = ?",
        ('30.01.1959', 733275095)
    )
    
    conn.commit()
    print(f"✅ Обновлено строк: {cursor.rowcount}")
    
    # Проверяем, что обновилось
    cursor.execute("SELECT telegram_id, fio, birth_date FROM users WHERE telegram_id = ?", (733275095,))
    row = cursor.fetchone()
    if row:
        print(f"📋 Проверка: ID={row[0]}, Имя={row[1]}, Дата={row[2]}")
    else:
        print("❌ Пользователь не найден!")
    
    conn.close()

if __name__ == "__main__":
    fix_birth()