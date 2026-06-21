# set_admin_partner.py
from database import get_connection

def set_admin_partner():
    admin_id = 258670125  # или ваш ID
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'partner' WHERE telegram_id = ?", (admin_id,))
    conn.commit()
    print(f"✅ Админу {admin_id} установлена роль 'partner'")
    conn.close()

if __name__ == "__main__":
    set_admin_partner()