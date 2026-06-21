# delete_user.py
from database import get_connection

def delete_user():
    user_id = 7878181865  # Ваш Telegram ID (тот, кто зарегистрирован как приглашённый)
    # Или другой ID, который хотите удалить
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        print(f"👤 Найден пользователь: {user['fio']} (ID: {user['telegram_id']})")
        
        # Удаляем пользователя
        cursor.execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))
        conn.commit()
        print(f"✅ Пользователь {user_id} удалён из базы")
        
        # Также удаляем из корзины, если есть
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
        
        # Удаляем из событий
        cursor.execute("DELETE FROM events WHERE telegram_id = ?", (user_id,))
        conn.commit()
    else:
        print(f"❌ Пользователь {user_id} не найден")
    
    # Показываем оставшихся пользователей
    cursor.execute("SELECT telegram_id, fio FROM users")
    users = cursor.fetchall()
    print("\n📋 Оставшиеся пользователи:")
    for u in users:
        print(f"   - {u['fio']} (ID: {u['telegram_id']})")
    
    conn.close()

if __name__ == "__main__":
    delete_user()