# fix_referrals_table.py
import sqlite3

def fix_referrals():
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()
    
    # Проверяем, есть ли таблица referrals
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
    if cursor.fetchone():
        print("✅ Таблица referrals уже существует")
    else:
        print("🔧 Создаём таблицу referrals...")
        cursor.execute("""
            CREATE TABLE referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sponsor_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, sponsor_id)
            )
        """)
        
        cursor.execute("CREATE INDEX idx_referrals_user_id ON referrals(user_id)")
        cursor.execute("CREATE INDEX idx_referrals_sponsor_id ON referrals(sponsor_id)")
        conn.commit()
        print("✅ Таблица referrals создана")
    
    # Проверяем, есть ли данные
    cursor.execute("SELECT COUNT(*) FROM referrals")
    count = cursor.fetchone()[0]
    print(f"📊 В таблице referrals записей: {count}")
    
    conn.close()

if __name__ == "__main__":
    fix_referrals()