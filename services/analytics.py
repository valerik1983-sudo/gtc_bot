import sqlite3
from datetime import datetime
from database import get_connection

def log_ai_dialog(user_id, user_message, ai_response, topic=None, products=None, forwarded_to_mentor=False):
    """
    Логирует диалог с AI для аналитики.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_message TEXT,
            ai_response TEXT,
            topic TEXT,
            products TEXT,
            forwarded_to_mentor INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO ai_analytics (user_id, user_message, ai_response, topic, products, forwarded_to_mentor)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, user_message, ai_response, topic, products, 1 if forwarded_to_mentor else 0))
    conn.commit()
    conn.close()

def get_analytics_summary():
    """Возвращает сводку по аналитике."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ai_analytics")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ai_analytics WHERE forwarded_to_mentor = 1")
    forwarded = cursor.fetchone()[0]
    cursor.execute("SELECT topic, COUNT(*) FROM ai_analytics WHERE topic IS NOT NULL GROUP BY topic ORDER BY COUNT(*) DESC")
    topics = cursor.fetchall()
    cursor.execute("SELECT products, COUNT(*) FROM ai_analytics WHERE products IS NOT NULL GROUP BY products ORDER BY COUNT(*) DESC")
    products = cursor.fetchall()
    conn.close()
    return {
        "total": total,
        "forwarded": forwarded,
        "topics": topics,
        "products": products
    }