import json
import sqlite3
from typing import Optional, Dict, Any
from database import get_connection

class ProfileManager:
    def get_profile(self, user_id: int) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return {
            "user_id": user_id,
            "name": None,
            "age": None,
            "city": None,
            "health_goals": None,
            "business_goals": None,
            "main_interests": None,
            "health_issues": None,
            "funnel_stage": None,
            "last_intent": None,
            "suggested_next_step": None,
        }

    def update_profile(self, user_id: int, updates: Dict[str, Any]):
        conn = get_connection()
        cursor = conn.cursor()
        fields = []
        values = []
        for key, value in updates.items():
            if value is not None and key != "user_id":
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
                fields.append(f"{key} = ?")
                values.append(value)
        if not fields:
            return
        values.append(user_id)
        query = f"UPDATE user_profiles SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
        cursor.execute(query, values)
        if cursor.rowcount == 0:
            # Если профиля нет – создаём
            columns = ", ".join(updates.keys())
            placeholders = ", ".join(["?"] * len(updates))
            sql = f"INSERT INTO user_profiles (user_id, {columns}) VALUES (?, {placeholders})"
            values = [user_id] + list(updates.values())
            cursor.execute(sql, values)
        conn.commit()
        conn.close()

# Глобальный экземпляр
profile_manager = ProfileManager()