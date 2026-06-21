# check_admin.py
from database import get_connection

def check_admin():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ваш Telegram ID - замените на свой
    your_id = 7878181865
    
    cursor.execute("SELECT * FROM admins WHERE telegram_id = ?", (your_id,))
    admin = cursor.fetchone()
    
    if admin:
        print(f"✅ Вы админ! ID: {admin['telegram_id']}")
    else:
        print(f"❌ Вы НЕ админ. Добавляем...")
        cursor.execute("INSERT INTO admins (telegram_id) VALUES (?)", (your_id,))
        conn.commit()
        print("✅ Теперь вы админ")
    
    # Показываем всех админов
    cursor.execute("SELECT telegram_id FROM admins")
    admins = cursor.fetchall()
    print(f"📋 Все админы: {[a['telegram_id'] for a in admins]}")
    
    conn.close()

if __name__ == "__main__":
    check_admin()