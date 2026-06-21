# check_user_sponsor.py
from database import get_connection

def check_user():
    user_id = 7878181865
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем поле sponsor_id в таблице users
    cursor.execute("SELECT telegram_id, fio, sponsor_id FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        print(f"👤 Пользователь: {user['fio']}")
        print(f"   telegram_id: {user['telegram_id']}")
        print(f"   sponsor_id в users: {user['sponsor_id']}")
    else:
        print(f"❌ Пользователь {user_id} не найден")
    
    # Проверяем таблицу referrals
    cursor.execute("SELECT * FROM referrals WHERE user_id = ?", (user_id,))
    referral = cursor.fetchone()
    
    if referral:
        print(f"   sponsor_id в referrals: {referral['sponsor_id']}")
    else:
        print(f"   Запись в referrals: отсутствует")
    
    conn.close()

if __name__ == "__main__":
    check_user()