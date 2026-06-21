from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Bot

from database import get_user, get_sponsor, create_consultation, add_event, get_last_consultation, is_admin, get_referrals_count
from keyboards import get_main_menu
from sponsor_inline import consultation_keyboard

router = Router()

# Хранилище для данных консультации
consult_data = {}


@router.message(Command("consult"))
async def consultation_start(message: Message):
    print("🔴🔴🔴 /consult ВЫЗВАН 🔴🔴🔴")
    user = get_user(message.from_user.id)
    print(f"🔴 user = {user}")
    if not user:
        await message.answer("📝 Для консультации необходимо зарегистрироваться.\n\nНажмите /start и заполните анкету.")
        return
    consult_data[message.from_user.id] = {"step": 1}
    await message.answer("💬 Напишите тему вашей консультации:")


@router.message()
async def consultation_step(message: Message, bot: Bot):
    if message.text.startswith('/'):
        return

    user_id = message.from_user.id
    if user_id not in consult_data:
        return
    
    data = consult_data[user_id]
    step = data.get("step")
    
    if step == 1:
        data["topic"] = message.text
        data["step"] = 2
        await message.answer("📱 Введите ваш номер телефона:")
    elif step == 2:
        data["phone"] = message.text
        data["step"] = 3
        await message.answer("⏰ Когда вам удобно связаться?")
    elif step == 3:
        data["time"] = message.text
        
        user = get_user(user_id)
        sponsor = get_sponsor(user_id)
        sponsor_id = sponsor["sponsor_id"] if sponsor else None
        
        create_consultation(
            client_telegram_id=user_id,
            sponsor_telegram_id=sponsor_id,
            topic=data["topic"],
            phone=data["phone"],
            preferred_time=data["time"]
        )
        add_event(user_id, "consultation", "Создана консультация")
        consultation = get_last_consultation(user_id)
        team_count = get_referrals_count(user_id)
        
        await message.answer(
            "✅ Запрос отправлен наставнику.\n\nС вами скоро свяжутся.",
            reply_markup=get_main_menu(True, team_count > 0, is_admin(user_id))
        )
        
        if sponsor_id:
            sponsor_user = get_user(int(sponsor_id))
            if sponsor_user:
                try:
                    await bot.send_message(
                        sponsor_user["telegram_id"],
                        f"🔥 Новая консультация\n\nКлиент: {user['fio']}\nТелефон: {data['phone']}\n\n"
                        f"Тема: {data['topic']}\n\nУдобное время: {data['time']}",
                        reply_markup=consultation_keyboard(consultation["id"])
                    )
                except Exception:
                    pass
        
        del consult_data[user_id]