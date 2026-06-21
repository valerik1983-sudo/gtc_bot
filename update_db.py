from database import get_connection

def add_columns():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Добавляем новые колонки, если их ещё нет
    cursor.execute("PRAGMA table_info(consultations)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    if "reminder_sent" not in existing_columns:
        cursor.execute("ALTER TABLE consultations ADD COLUMN reminder_sent INTEGER DEFAULT 0")
        print("✅ Добавлена колонка reminder_sent")
    
    if "complaint_button_shown" not in existing_columns:
        cursor.execute("ALTER TABLE consultations ADD COLUMN complaint_button_shown INTEGER DEFAULT 0")
        print("✅ Добавлена колонка complaint_button_shown")
    
    if "complaint_sent_at" not in existing_columns:
        cursor.execute("ALTER TABLE consultations ADD COLUMN complaint_sent_at TIMESTAMP")
        print("✅ Добавлена колонка complaint_sent_at")
    
    conn.commit()
    conn.close()
    print("✅ Готово!")

if __name__ == "__main__":
    add_columns()