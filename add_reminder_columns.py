# add_reminder_columns.py
from database import get_connection

def add_columns():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Для заказов - когда было последнее напоминание о корзине
    try:
        cursor.execute("ALTER TABLE cart ADD COLUMN reminder_sent INTEGER DEFAULT 0")
        print("✅ cart.reminder_sent добавлена")
    except:
        print("⚠️ cart.reminder_sent уже существует")
    
    # Для пользователей - когда наставник последний раз писал
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_mentor_contact TIMESTAMP")
        print("✅ users.last_mentor_contact добавлена")
    except:
        print("⚠️ users.last_mentor_contact уже существует")
    
    # Для консультаций - сколько раз отправляли напоминание
    try:
        cursor.execute("ALTER TABLE consult_requests ADD COLUMN reminder_count INTEGER DEFAULT 0")
        print("✅ consult_requests.reminder_count добавлена")
    except:
        print("⚠️ consult_requests.reminder_count уже существует")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()