from database import get_connection

def add_story_column():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE symptoms ADD COLUMN story_key TEXT")
        print("✅ Добавлена колонка story_key")
    except:
        print("Колонка story_key уже существует")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_story_column()