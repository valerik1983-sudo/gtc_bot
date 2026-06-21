from database import get_connection

def create_symptoms_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symptoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        title TEXT,
        description TEXT,
        products TEXT,
        category TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Таблица symptoms создана")

if __name__ == "__main__":
    create_symptoms_table()