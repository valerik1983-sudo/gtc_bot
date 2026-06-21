# remove_admin.py
from database import get_connection

def remove_admin():
    user_id = 7878181865
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли пользователь в админах
    cursor.execute("SELECT * FROM admins WHERE telegram_id = ?", (user_id,))
    admin = cursor.fetchone()
    
    if admin:
        cursor.execute("DELETE FROM admins WHERE telegram_id = ?", (user_id,))
        conn.commit()
        print(f"✅ Пользователь {user_id} удалён из админов")
    else:
        print(f"❌ Пользователь {user_id} не является админом")
    
    # Показываем оставшихся админов
    cursor.execute("SELECT telegram_id FROM admins")
    admins = cursor.fetchall()
    print(f"📋 Оставшиеся админы: {[a['telegram_id'] for a in admins]}")
    
    conn.close()

if __name__ == "__main__":
    remove_admin()