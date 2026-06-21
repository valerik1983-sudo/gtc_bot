# Создай файл seed_prices.py
from database import set_product_price

prices = {
    "🍊 Perfecto Lux": 2400,
    "🍒 Vitality Lux": 2400,
    "🧠 Smart Lux": 2400,
    "⚡️ Energy Lux": 2400,
    "🛡️ ImmunoLux": 2400,
    "🦷 Luxury Day": 1200,
    "🌙 Luxury Night": 1200,
    "🌰 Harmony Lux": 2400,
    "🧂 Wellness Lux": 2400,
    "💧 May": 4800,
    "💦 Pavlov Spring": 21600,
    "🌿 Delight": 3600,
}

for name, price in prices.items():
    set_product_price(name, price)
    print(f"✅ {name}: {price} руб.")