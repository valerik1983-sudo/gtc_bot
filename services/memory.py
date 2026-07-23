import sqlite3
from typing import List, Dict
from database import get_connection

class MemoryManager:
    def get_history(self, user_id: int, limit: int = 10) -> List[Dict[str, str]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM conversation_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        # Возвращаем в правильном порядке (от старого к новому)
        history = []
        for row in reversed(rows):
            history.append({"role": row["role"], "content": row["content"]})
        return history

    def add_message(self, user_id: int, role: str, content: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversation_history (user_id, role, content)
            VALUES (?, ?, ?)
        """, (user_id, role, content))
        conn.commit()
        conn.close()

    def clear(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversation_history WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

# Глобальный экземпляр (используем тот же объект)
memory = MemoryManager()