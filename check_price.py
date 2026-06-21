from database import get_connection

def check_prices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price FROM product_prices")
    rows = cursor.fetchall()
    conn.close()
    
    print("Цены в БД:")
    for row in rows:
        print(f"  '{row['product_name']}' → {row['price']} руб.")

if __name__ == "__main__":
    check_prices()