# check_programs_in_products.py
from database import get_connection

def check():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, programs FROM products WHERE programs IS NOT NULL")
    products = cursor.fetchall()
    for p in products:
        print(f"Товар: {p['name']}")
        print(f"Программы: {p['programs']}")
        print("---")
    conn.close()

if __name__ == "__main__":
    check()