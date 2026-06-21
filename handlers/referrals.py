from aiogram import Router
from aiogram.filters import StateFilter  # добавьте в начало файла
from aiogram.types import Message
from database import (
    get_user,
    get_sponsor_chain,
    get_referrals_count,
    get_total_referrals_count,
    get_referrals
)

router = Router()


@router.message(lambda m: m.text == "🌳 Моя структура")
async def show_my_hierarchy(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь.")
        return

    # Кто выше
    chain = get_sponsor_chain(message.from_user.id)

    if chain:
        chain_text = " → ".join([f"{s['fio']}" for s in chain])
        chain_text = f"⬆️ Ваши наставники:\n{chain_text}\n\n"
    else:
        chain_text = "⬆️ Вы являетесь верхним наставником в своей структуре.\n\n"

    # Кто ниже
    total_referrals = get_total_referrals_count(message.from_user.id)
    direct_referrals = get_referrals_count(message.from_user.id)

    # Первые 10 прямых рефералов
    referrals = get_referrals(message.from_user.id)[:10]

    if referrals:
        referrals_text = "⬇️ Ваши приглашённые (первые 10):\n"
        for ref in referrals:
            status_icon = {
                "new": "🆕",
                "work": "🟡",
                "client": "🟢",
                "partner": "💎",
                "failed": "🔴"
            }.get(ref["status"], "⚪")

            referrals_text += f"{status_icon} {ref['fio']}\n"
    else:
        referrals_text = "⬇️ У вас пока нет приглашённых.\n"

    await message.answer(
        f"🌳 **Ваша структура**\n\n"
        f"{chain_text}"
        f"📊 **Статистика:**\n"
        f"• Прямых приглашений: {direct_referrals}\n"
        f"• Всего в структуре: {total_referrals}\n\n"
        f"{referrals_text}\n\n"
        f"💡 *Приглашайте новых партнёров через свою ссылку*",
        parse_mode="Markdown"
    )

async def need_attention(message: Message):
    user_id = message.from_user.id
    
    # Получаем пользователей, требующих внимания (старые лиды)
    users = get_users_need_attention(user_id)
    
    # Получаем активные консультации без ответа старше 6 часов
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT cr.*, u.fio, u.phone 
        FROM consult_requests cr
        JOIN users u ON cr.user_id = u.telegram_id
        WHERE cr.sponsor_id = ? 
        AND cr.status = 'active'
        AND cr.last_message_at IS NULL
        AND datetime(cr.created_at) <= datetime('now', '-6 hours')
    """, (user_id,))
    
    consultations = cursor.fetchall()
    conn.close()
    
    if not users and not consultations:
        await message.answer("Сейчас нет людей и консультаций, требующих внимания ✅")
        return
    
    text = "⏰ **Требуют внимания**\n\n"
    
    # Добавляем старых лидов
    if users:
        text += "📋 **Люди без ответа:**\n"
        for user in users:
            text += f"👤 {user['fio']}\n📊 Статус: {user['status']}\n📱 {user['phone']}\n\n"
    
    # Добавляем старые консультации
    if consultations:
        text += "💬 **Консультации без ответа:**\n"
        for consult in consultations:
            text += f"👤 {consult['fio']}\n📞 {consult['phone']}\n"
            text += f"🆔 Консультация #{consult['id']}\n"
            text += f"📅 {consult['created_at']}\n\n"
    
    await message.answer(text, parse_mode="Markdown")    

@router.callback_query(lambda c: c.data.startswith("answer_consult_"))
async def answer_consultation(callback: CallbackQuery, state: FSMContext):
    consult_id = int(callback.data.split("_")[2])
    await state.update_data(answer_consult_id=consult_id)
    await state.set_state("waiting_consult_answer")
    await callback.message.answer("✏️ Введите ответ для пользователя:")
    await callback.answer()


@router.message(StateFilter("waiting_consult_answer"))
async def send_consult_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    consult_id = data.get("answer_consult_id")
    
    from database import get_connection, add_event
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем пользователя из консультации
    cursor.execute("SELECT user_id FROM consult_requests WHERE id = ?", (consult_id,))
    result = cursor.fetchone()
    
    if result:
        user_id = result[0]
        
        # Отправляем ответ
        await message.bot.send_message(
            user_id,
            f"📩 **Ответ администратора:**\n\n{message.text}\n\n"
            f"Извините за долгое ожидание. Если у вас остались вопросы, "
            f"вы можете снова обратиться к наставнику."
        )
        
        # Обновляем статус
        cursor.execute("UPDATE consult_requests SET status = 'answered' WHERE id = ?", (consult_id,))
        conn.commit()
        
        add_event(user_id, "consult", f"Администратор ответил на консультацию #{consult_id}")
        
        await message.answer("✅ Ответ отправлен пользователю!")
    else:
        await message.answer("❌ Консультация не найдена")
    
    conn.close()
    await state.clear()    

async def need_attention_with_buttons(message: Message):
    user_id = message.from_user.id
    
    # Получаем активные консультации без ответа старше 6 часов
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT cr.*, u.fio, u.phone 
        FROM consult_requests cr
        JOIN users u ON cr.user_id = u.telegram_id
        WHERE cr.sponsor_id = ? 
        AND cr.status = 'active'
        AND cr.last_message_at IS NULL
        AND datetime(cr.created_at) <= datetime('now', '-6 hours')
    """, (user_id,))
    
    consultations = cursor.fetchall()
    conn.close()
    
    if not consultations:
        await message.answer("Сейчас нет консультаций, требующих внимания ✅")
        return
    
    # Отправляем каждую консультацию с кнопкой
    for consult in consultations:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"answer_consult_{consult['id']}")]
        ])
        
        await message.answer(
            f"💬 **Консультация #{consult['id']}**\n\n"
            f"👤 Пользователь: {consult['fio']}\n"
            f"📞 Телефон: {consult['phone']}\n"
            f"📅 Создана: {consult['created_at']}\n\n"
            f"⚠️ Нет ответа более 6 часов!",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )    

async def my_data(message: Message):
    """Показать данные пользователя"""
    from database import get_user
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы в системе.\n\nНажмите '📝 Регистрация' для регистрации.")
        return
    
    text = (
        f"📝 **Ваши данные:**\n\n"
        f"👤 **ФИО:** {user.get('fio', 'Не указано')}\n"
        f"🎂 **Дата рождения:** {user.get('birth_date', 'Не указана')}\n"
        f"📱 **Телефон:** {user.get('phone', 'Не указан')}\n"
        f"🏙️ **Город:** {user.get('city', 'Не указан')}\n"
        f"👫 **Пол:** {user.get('gender', 'Не указан')}\n"
        f"📊 **Статус:** {user.get('status', 'Новый')}\n\n"
        f"🆔 **Ваш ID:** `{message.from_user.id}`"
    )
    
    # Добавляем информацию о наставнике
    from database import get_sponsor
    sponsor = get_sponsor(message.from_user.id)
    if sponsor and sponsor.get('sponsor_id'):
        sponsor_user = get_user(sponsor['sponsor_id'])
        if sponsor_user:
            text += f"\n\n👨‍🏫 **Ваш наставник:** {sponsor_user.get('fio', 'Неизвестно')}"
    
    await message.answer(text, parse_mode="Markdown")        


    