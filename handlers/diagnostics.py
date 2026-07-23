# handlers/diagnostics.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter


from states import Diagnostics
from data.diagnostics_data import (
    QUESTIONS, RESULTS, get_result_by_score, 
    get_age_group, RECOMMENDATIONS
)
from database import (
    get_user, save_diagnostic_result, 
    get_diagnostic_history, is_admin,
    get_referrals_count, add_event,
    create_gift_claim,       get_gift_claim, 
)
from keyboards import get_main_menu

router = Router()

# Временное хранилище для незарегистрированных пользователей
temp_diagnostic_data = {}


@router.message(F.text == "🔬 Пройти диагностику")
async def start_diagnostics(message: Message, state: FSMContext):
    """Запуск диагностики"""
    user = get_user(message.from_user.id)
    
    # Проверяем, есть ли уже результат
    history = get_diagnostic_history(message.from_user.id)
    
    if history and len(history) > 0:
        # Показываем последний результат
        last = history[0]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Пройти заново", callback_data="diagnostics_restart")],
            [InlineKeyboardButton(text="📊 Сравнить с прошлым", callback_data="diagnostics_compare")]
        ])
        
        await message.answer(
            f"📊 **Вы уже проходили диагностику!**\n\n"
            f"Последний результат: {last['total_score']} баллов\n"
            f"Дата: {last['created_at'][:16]}\n\n"
            f"Хотите пройти заново или сравнить с прошлым результатом?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Начинаем диагностику
    await state.set_state(Diagnostics.waiting_question)
    await state.update_data(current_q=0, answers={})
    
    # Если пользователь не зарегистрирован, сохраняем временные данные
    if not user:
        temp_diagnostic_data[message.from_user.id] = {
            "started": True,
            "registered": False
        }
    
    await send_question(message, state, 0)


@router.callback_query(F.data == "diagnostics_restart")
async def restart_diagnostics(callback: CallbackQuery, state: FSMContext):
    """Перезапуск диагностики"""
    await callback.message.delete()
    await start_diagnostics(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "diagnostics_compare")
async def compare_diagnostics(callback: CallbackQuery):
    """Сравнение текущего и предыдущего результатов"""
    history = get_diagnostic_history(callback.from_user.id)
    
    if len(history) < 2:
        await callback.message.answer("📊 У вас пока только один результат. Пройдите диагностику заново, чтобы сравнить.")
        await callback.answer()
        return
    
    current = history[0]
    previous = history[1]
    
    diff = current['total_score'] - previous['total_score']
    diff_emoji = "📈" if diff > 0 else "📉" if diff < 0 else "➖"
    
    text = (
        f"📊 **Сравнение результатов диагностики**\n\n"
        f"🔄 **Текущий результат:** {current['total_score']} баллов ({current['created_at'][:10]})\n"
        f"🔄 **Предыдущий результат:** {previous['total_score']} баллов ({previous['created_at'][:10]})\n\n"
        f"**Изменение:** {diff_emoji} {diff} баллов\n\n"
    )
    
    if diff > 5:
        text += "🌟 Отличный прогресс! Продолжайте в том же духе!"
    elif diff < -5:
        text += "⚠️ Обратите внимание на свой образ жизни. Возможно, стоит пересмотреть режим."
    else:
        text += "📌 Ваш уровень стабилен. Попробуйте внести небольшие изменения, чтобы улучшить результат."
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("diag_ans_"))
async def answer_question(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос"""
    data = await state.get_data()
    current_q = data.get("current_q", 0)
    answers = data.get("answers", {})
    
    # Разбираем callback_data
    parts = callback.data.split("_")
    q_id = int(parts[2])
    score = int(parts[3])
    
    # Сохраняем ответ
    answers[q_id] = score
    await state.update_data(answers=answers)
    
    # Переход к следующему вопросу
    next_q = current_q + 1
    
    if next_q < len(QUESTIONS):
        await state.update_data(current_q=next_q)
        await send_question(callback.message, state, next_q)
    else:
        # Диагностика завершена
        await finish_diagnostics(callback, state)
    
    await callback.answer()


async def send_question(message: Message, state: FSMContext, q_index: int):
    """Отправка вопроса"""
    question = QUESTIONS[q_index]
    
    keyboard = []
    for option in question["options"]:
        keyboard.append([
            InlineKeyboardButton(
                text=option["text"],
                callback_data=f"diag_ans_{question['id']}_{option['score']}"
            )
        ])
    
    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="diag_cancel")])
    
    await message.answer(
        f"🔬 **Вопрос {q_index + 1} из {len(QUESTIONS)}**\n\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "diag_cancel")
async def cancel_diagnostics(callback: CallbackQuery, state: FSMContext):
    """Отмена диагностики"""
    await state.clear()
    
    # Очищаем временные данные
    if callback.from_user.id in temp_diagnostic_data:
        del temp_diagnostic_data[callback.from_user.id]
    
    await callback.message.delete()
    await callback.message.answer("❌ Диагностика отменена.")
    await callback.answer()


async def finish_diagnostics(callback: CallbackQuery, state: FSMContext):
    """Завершение диагностики"""
    data = await state.get_data()
    answers = data.get("answers", {})
    
    # Считаем сумму баллов
    total_score = sum(answers.values())
    
    # Определяем результат
    result_key, result = get_result_by_score(total_score)
    
    # Сохраняем результат в БД
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    # Сохраняем диагностику
    save_diagnostic_result(
        user_id=user_id,
        user_fio=user.get('fio', 'Не зарегистрирован') if user else 'Не зарегистрирован',
        total_score=total_score,
        result_key=result_key,
        answers=answers
    )
    
    # Записываем событие
    if user:
        add_event(user_id, "diagnostic", f"Пройдена диагностика: {total_score} баллов ({result['title']})")
    
    # ===== ПОДАРОК ЗА ДИАГНОСТИКУ =====
    # Проверяем, есть ли уже неиспользованный подарок у пользователя
    existing_gift = get_gift_claim(user_id)
    if not existing_gift:
        # Если нет, создаём новый подарок
        # diagnostic_id можно не передавать, или передать последний ID диагностики
        # Получаем последнюю диагностику
        diag_history = get_diagnostic_history(user_id, limit=1)
        diagnostic_id = diag_history[0]['id'] if diag_history else None
        create_gift_claim(user_id, diagnostic_id)
    
    # Если подарок уже есть, но он не использован, то ничего не делаем
    # (повторно подарок не выдаём)
    
    # Показываем сообщение о подарке (для всех, даже если подарок уже был, но не использован — покажем ещё раз?)
    # Лучше показывать только если подарок ещё не использован
    gift_claim = get_gift_claim(user_id)
    if gift_claim:
        gift_text = (
            "🎁 **Поздравляем!**\n\n"
            "Вы прошли диагностику и получаете **подарок** при первом заказе! 🎉\n\n"
            "При оформлении заказа вам будет доступна отметка о подарке.\n"
            "Уточните у наставника полные условия получения подарка.\n\n"
            "💡 Если у вас ещё нет наставника, зарегистрируйтесь, и он будет назначен."
        )
        await callback.message.answer(gift_text, parse_mode="Markdown")
    
    # Формируем текст результата
    text = (
        f"🔬 **Результат диагностики**\n\n"
        f"{result['emoji']} **{result['title']}**\n"
        f"{result['description']}\n\n"
        f"📊 **Ваш результат:** {total_score} из {len(QUESTIONS) * 4} баллов\n\n"
    )
    
    # Добавляем рекомендации в зависимости от возраста
    age_answer = None
    for q_id, score in answers.items():
        question = QUESTIONS[q_id - 1] if q_id - 1 < len(QUESTIONS) else None
        if question and "Сколько вам лет?" in question["text"]:
            # Находим выбранный вариант
            for option in question["options"]:
                if option["score"] == score:
                    age_answer = option["text"]
                    break
    
    if age_answer:
        age_group = get_age_group(age_answer)
        if age_group in RECOMMENDATIONS:
            text += f"\n---\n\n{RECOMMENDATIONS[age_group]['text']}"
    
    # Формируем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Кнопка "Пройти заново" — всегда доступна
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="📊 Пройти заново", callback_data="diagnostics_restart")])

    # Кнопка "Главное меню" — всегда доступна
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="diag_to_main")])

    # Если пользователь зарегистрирован — добавляем кнопку рекомендаций
    if user:
        keyboard.inline_keyboard.insert(0, [InlineKeyboardButton(text="📋 Получить персональные рекомендации", callback_data="diag_recommendations")])
    else:
        # Если не зарегистрирован — добавляем кнопку регистрации
        text += "\n\n🔐 **Чтобы получить полный разбор вашего профиля, персональные рекомендации и доступ ко всем возможностям — подпишитесь (это займёт 1 минуту).**"
        keyboard.inline_keyboard.insert(0, [InlineKeyboardButton(text="📝 Подписаться", callback_data="diag_register")])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.clear()
    
    # Очищаем временные данные
    if callback.from_user.id in temp_diagnostic_data:
        del temp_diagnostic_data[callback.from_user.id]
    
    await callback.answer()


@router.callback_query(F.data == "diag_recommendations")
async def get_recommendations(callback: CallbackQuery, state: FSMContext):
    """Получить персональные рекомендации (или предложить регистрацию)"""
    user = get_user(callback.from_user.id)
    
    # Если пользователь не зарегистрирован — предлагаем регистрацию
    if not user:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="diag_register_recommend")],
            [InlineKeyboardButton(text="🔙 Назад к результату", callback_data="diag_back_to_result")]
        ])
        await callback.message.answer(
            "📋 **Для получения персональных рекомендаций необходимо зарегистрироваться.**\n\n"
            "Регистрация займёт всего минуту и даст доступ ко всем возможностям бота.\n\n"
            "Нажмите «Зарегистрироваться», чтобы продолжить.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    # ----- Далее код для зарегистрированных (без изменений) -----
    history = get_diagnostic_history(callback.from_user.id)
    if not history:
        await callback.message.answer("❌ Сначала пройдите диагностику.")
        await callback.answer()
        return
    
    last = history[0]
    answers = last.get('answers', {})
    
    # Поиск возраста
    age_answer = None
    for q_id_str, score in answers.items():
        q_id = int(q_id_str)
        if 1 <= q_id <= len(QUESTIONS):
            question = QUESTIONS[q_id - 1]
            if "Сколько вам лет?" in question["text"]:
                for option in question["options"]:
                    if option["score"] == score:
                        age_answer = option["text"]
                        break
                if age_answer:
                    break
    
    result_key = last.get('result_key', 'medium')
    result = RESULTS.get(result_key, RESULTS["medium"])
    
    text = (
        f"📋 **Персональные рекомендации**\n\n"
        f"{result['emoji']} {result['title']}\n"
        f"{result['description']}\n\n"
    )
    
    if age_answer:
        age_group = get_age_group(age_answer)
        if age_group in RECOMMENDATIONS:
            text += f"\n{RECOMMENDATIONS[age_group]['text']}"
    else:
        text += "\n📌 Рекомендуем обратиться к наставнику для получения персональных рекомендаций."
    
    text += "\n\n💡 Для получения индивидуальной консультации обратитесь к вашему наставнику."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Связаться с наставником", callback_data="diag_consult")],
        [InlineKeyboardButton(text="🔙 Назад к результату", callback_data="diag_back_to_result")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    
@router.callback_query(F.data == "diag_register_recommend")
async def register_from_recommend(callback: CallbackQuery, state: FSMContext):
    """Запуск регистрации с флагом, что после неё нужно показать результат диагностики"""
    # Сохраняем флаг, что после регистрации нужно вернуться к диагностике
    await state.update_data(pending_recommendations=True)
    
    # Запускаем регистрацию (импортируем из menu)
    from handlers.menu import start_registration
    await start_registration(callback.message, state)
    await callback.answer()    


@router.callback_query(F.data == "diag_register")
async def register_after_diagnostic(callback: CallbackQuery, state: FSMContext):
    """Регистрация после диагностики"""
    from handlers.menu import start_registration
    await start_registration(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "diag_to_main")
async def diag_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    user = get_user(callback.from_user.id)
    registered = user is not None
    has_team = get_referrals_count(callback.from_user.id) > 0 if registered else False
    is_admin_user = is_admin(callback.from_user.id)
    
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu(registered, has_team, is_admin_user)
    )
    await callback.answer()


@router.callback_query(F.data == "diag_consult")
async def diag_consult(callback: CallbackQuery):
    """Связь с наставником после диагностики"""
    from config import CONSULT_BOT_USERNAME
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Перейти к консультации", url=f"https://t.me/{CONSULT_BOT_USERNAME}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="diag_back_to_result")]
    ])
    await callback.message.answer(
        "💬 Для получения индивидуальной консультации перейдите в консультационный бот.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "diag_back_to_result")
async def back_to_result(callback: CallbackQuery):
    """Возврат к результату диагностики"""
    history = get_diagnostic_history(callback.from_user.id)
    
    if not history:
        await callback.message.answer("❌ Результат не найден.")
        await callback.answer()
        return
    
    last = history[0]
    total_score = last['total_score']
    result_key = last.get('result_key', 'medium')
    result = RESULTS.get(result_key, RESULTS["medium"])
    
    text = (
        f"🔬 **Результат диагностики**\n\n"
        f"{result['emoji']} **{result['title']}**\n"
        f"{result['description']}\n\n"
        f"📊 **Ваш результат:** {total_score} из {len(QUESTIONS) * 4} баллов\n\n"
    )
    
    user = get_user(callback.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Получить персональные рекомендации", callback_data="diag_recommendations")],
        [InlineKeyboardButton(text="📊 Пройти заново", callback_data="diagnostics_restart")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="diag_to_main")]
    ])
    
    if not user:
        keyboard.inline_keyboard.insert(0, [
            InlineKeyboardButton(text="📝 Подписаться", callback_data="diag_register")
        ])
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()