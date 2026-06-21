from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states import MentorMessage, ClientReply
from database import (
    get_user, get_sponsor, create_consultation, add_event,
    get_last_consultation, is_admin, get_referrals_count,
    get_consultation, update_last_contact, get_active_consultation,
    update_consultation_status, get_consultation_stats,
    get_consultations_by_status, add_user
)
from keyboards import get_main_menu, consultations_menu_keyboard
from sponsor_inline import consultation_keyboard
from inline_keyboards import reply_to_mentor_keyboard

router = Router()


async def registration_start(message: Message, state: FSMContext):
    """Запускает регистрацию (может быть вызвана из других модулей)"""
    from states import Registration
    await state.set_state(Registration.fio)
    await message.answer(
        "📝 **Регистрация**\n\nВведите ваше ФИО:",
        parse_mode="Markdown"
    )


# Временное хранилище для консультации
temp_consultation = {}


@router.message(F.text == "💬 Получить консультацию")
async def consultation_start(message: Message):
    print("🔴🔴🔴 КНОПКА НАЖАТА, consultation_start ВЫЗВАН")
    user = get_user(message.from_user.id)
    print(f"🔴 user = {user}")
    if not user:
        await message.answer("📝 Для консультации необходимо зарегистрироваться.\n\nНажмите /start и заполните анкету.")
        return
    temp_consultation[message.from_user.id] = {"user_id": message.from_user.id}
    await message.answer("💬 Напишите тему вашей консультации:\n\nНапример: энергия, похудение, суставы, иммунитет...")
    print("🔴 СООБЩЕНИЕ ОТПРАВЛЕНО")


@router.message()
async def handle_consultation_flow(message: Message, bot: Bot):
    user_id = message.from_user.id
    
    # Если пользователь не в процессе консультации — просто выходим
    if user_id not in temp_consultation:
        return
    
    data = temp_consultation[user_id]
    
    if "topic" not in data:
        data["topic"] = message.text
        await message.answer("📱 Введите ваш номер телефона:")
        return
    
    if "phone" not in data:
        data["phone"] = message.text
        await message.answer("⏰ Когда вам удобно связаться?")
        return
    
    if "time" not in data:
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
                except Exception as e:
                    print("Ошибка отправки наставнику:", e)
        
        del temp_consultation[user_id]


@router.callback_query(lambda c: c.data.startswith("msg_"))
async def mentor_message_start(callback: CallbackQuery, state: FSMContext):
    consultation_id = int(callback.data.split("_")[1])
    consultation = get_consultation(consultation_id)
    if consultation:
        await state.update_data(client_id=consultation["client_telegram_id"])
        await state.set_state("waiting_message_to_client")
        await callback.message.answer("✏️ Введите сообщение для клиента:")
    else:
        await callback.message.answer("❌ Консультация не найдена")
    await callback.answer()


@router.message(StateFilter("waiting_message_to_client"))
async def send_to_client(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    client_id = data["client_id"]
    
    from inline_keyboards import reply_to_mentor_keyboard
    keyboard = reply_to_mentor_keyboard()
    
    await bot.send_message(
        client_id,
        f"📩 Сообщение от наставника:\n\n{message.text}",
        reply_markup=keyboard
    )
    await message.answer("✅ Сообщение отправлено клиенту!")
    await state.clear()


@router.callback_query(lambda c: c.data == "reply_to_mentor")
async def reply_to_mentor(callback: CallbackQuery, state: FSMContext):
    consultation = get_active_consultation(callback.from_user.id)
    if not consultation:
        await callback.answer("У вас нет активных обращений.")
        return
    await state.update_data(mentor_id=consultation["sponsor_telegram_id"], consultation_id=consultation["id"])
    await state.set_state(ClientReply.waiting_text)
    await callback.message.answer("✏️ Введите сообщение наставнику:")
    await callback.answer()


@router.message(StateFilter(ClientReply.waiting_text))
async def client_reply_to_mentor(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    mentor_id = data["mentor_id"]
    user = get_user(message.from_user.id)
    await bot.send_message(mentor_id, f"📩 Ответ клиента\n\nОт: {user['fio']}\n\n{message.text}")
    await message.answer("✅ Сообщение отправлено наставнику!")
    await state.clear()

@router.message(F.text == "🆘 Консультация")
async def consultation_menu(message: Message):
    from keyboards import consultation_submenu
    await message.answer(
        "🆘 Для получения консультации нажмите кнопку ниже:",
        reply_markup=consultation_submenu
    )     