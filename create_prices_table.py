from database import get_connection

def create_prices_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_prices (
        product_name TEXT PRIMARY KEY,
        price REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Таблица product_prices создана")

if __name__ == "__main__":
    create_prices_table()