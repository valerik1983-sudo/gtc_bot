# fix_programs.py
from database import get_connection

def fix():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Очищаем программы у всех товаров
    cursor.execute("UPDATE products SET programs = NULL")
    conn.commit()
    
    # Проверяем результат
    cursor.execute("SELECT name, programs FROM products WHERE programs IS NOT NULL")
    products = cursor.fetchall()
    
    if not products:
        print("✅ Все программы удалены из товаров")
    else:
        print("❌ Остались программы:")
        for p in products:
            print(f"   {p['name']}: {p['programs']}")
    
    conn.close()

if __name__ == "__main__":
    fix()