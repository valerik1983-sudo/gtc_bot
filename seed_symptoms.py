from database import add_symptom, get_connection

SYMPTOMS = [
    # Энергия
    ("energy_morning", "😴 Усталость утром", 
     "Часто связана с недостаточным восстановлением. Рекомендуем Vitality Lux.",
     "🍒 Vitality Lux,⚡️ Energy Lux", "energy", "vitality"),
    
    ("energy_day", "😵 Нет сил днем",
     "Energy Lux поможет быстро восстановить силы.", 
     "⚡️ Energy Lux,🍒 Vitality Lux", "energy", "energy"),
    
    ("energy_sport", "🏃 Энергия для спорта",
     "Energy Lux + Vitality Lux для активных тренировок.",
     "⚡️ Energy Lux,🍒 Vitality Lux", "energy", "energy"),
    
    ("energy_focus", "🧠 Концентрация",
     "Smart Lux поддержит мозг и улучшит концентрацию.",
     "🧠 Smart Lux", "energy", "smart"),
    
    # Контроль веса
    ("weight", "⚖️ Контроль веса",
     "Perfecto Lux + Wellness Lux помогут нормализовать обмен веществ.",
     "🍊 Perfecto Lux,🧂 Wellness Lux", "weight", "perfecto"),
    
    # Иммунитет
    ("immunity", "🛡️ Иммунитет",
     "ImmunoLux укрепит защитные силы организма.",
     "🛡️ ImmunoLux,🍊 Perfecto Lux", "immunity", "immuno"),
    
    # Суставы
    ("joints", "🦴 Суставы",
     "Wellness Lux поддержит здоровье суставов.",
     "🧂 Wellness Lux,💦 Pavlov Spring", "joints", "wellness"),
]

def seed_symptoms():
    conn = get_connection()
    cursor = conn.cursor()
    
    for s in SYMPTOMS:
        cursor.execute("""
            INSERT OR REPLACE INTO symptoms (name, title, description, products, category, story_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, s)
    
    conn.commit()
    conn.close()
    print("✅ Симптомы загружены в БД")

if __name__ == "__main__":
    seed_symptoms()