# check_referrals.py
from database import get_connection

def check_referrals():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM referrals")
    rows = cursor.fetchall()
    
    print("📋 Таблица referrals:")
    for row in rows:
        print(f"   user_id: {row['user_id']}, sponsor_id: {row['sponsor_id']}")
    
    conn.close()

if __name__ == "__main__":
    check_referrals()