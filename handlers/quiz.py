from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from handlers.income import get_generation_info, income_info_keyboard

from database import get_user, get_sponsor, add_event
from states import Quiz
from config import MAIN_BOT_TOKEN

router = Router()

# Вопросы и варианты ответов
QUESTIONS = {
    1: {
        "text": "💰 **Какую сумму дополнительного дохода вы считаете для себя интересной?**",
        "options": [
            ("До 10 000 ₽", 1),
            ("10 000 - 30 000 ₽", 2),
            ("30 000 - 50 000 ₽", 3),
            ("50 000 - 100 000 ₽", 4),
            ("Более 100 000 ₽", 5)
        ]
    },
    2: {
        "text": "💭 **Если бы у вас появился дополнительный доход 20–50 тыс. ₽ в месяц, что бы вы сделали в первую очередь?**",
        "options": [
            ("Закрыл(а) бы кредиты", 2),
            ("Отложил(а) бы на отпуск", 1),
            ("Инвестировал(а)", 3),
            ("Улучшил(а) качество жизни", 2),
            ("Мне это не особо интересно", 0)
        ]
    },
    3: {
        "text": "⏰ **Сколько времени вы готовы уделять дополнительному делу?**",
        "options": [
            ("Не готов(а)", 0),
            ("1–3 часа в неделю", 1),
            ("30–60 минут в день", 2),
            ("1–2 часа в день", 3),
            ("Более 2 часов в день", 4)
        ]
    },
    4: {
        "text": "🎯 **Что вам ближе?**",
        "options": [
            ("Продавать товары", 2),
            ("Общаться с людьми", 3),
            ("Обучаться новому", 2),
            ("Работать только онлайн", 1),
            ("Ничего из перечисленного", 0)
        ]
    },
    5: {
        "text": "💬 **Как вы относитесь к рекомендациям знакомым полезных товаров или услуг?**",
        "options": [
            ("Часто рекомендую", 3),
            ("Иногда", 2),
            ("Редко", 1),
            ("Никогда", 0)
        ]
    },
    6: {
        "text": "😟 **Что вас сейчас беспокоит больше всего?**",
        "options": [
            ("Не хватает денег", 2),
            ("Нет финансовой подушки", 2),
            ("Не нравится текущая работа", 1),
            ("Хочу больше свободного времени", 1),
            ("Меня всё устраивает", 0)
        ]
    }
}


def get_result_by_score(score):
    """Определяет результат по сумме баллов"""
    if score <= 5:
        return {
            "level": "low",
            "title": "Низкий интерес",
            "message": "Похоже, сейчас дополнительный доход не является вашим приоритетом.",
            "button_text": "👉 Узнать о продукции",
            "button_url": "https://t.me/gtcm_assistant_bot?start=products"
        }
    elif score <= 10:
        return {
            "level": "medium",
            "title": "Средний интерес",
            "message": "Возможно, вам будет интересен вариант дополнительного дохода без увольнения с основной работы.",
            "button_text": "👉 Посмотреть короткое видео",
            "button_url": "https://t.me/gtcm_assistant_bot?start=video"
        }
    else:
        return {
            "level": "high",
            "title": "Высокий интерес",
            "message": "Судя по ответам, вам может подойти модель дополнительного дохода через рекомендации и сопровождение клиентов.",
            "button_text": "👉 Получить консультацию",
            "button_url": "https://t.me/gtcm_consult_bot"
        }


def save_quiz_result(user_id, answers, score, result):
    """Сохраняет результат квиза в БД"""
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    import json
    answers_json = json.dumps(answers, ensure_ascii=False)
    
    cursor.execute("""
        INSERT OR REPLACE INTO quiz_results (user_id, answers, total_score, result)
        VALUES (?, ?, ?, ?)
    """, (user_id, answers_json, score, result))
    
    conn.commit()
    conn.close()


def has_completed_quiz(user_id):
    """Проверяет, проходил ли пользователь квиз"""
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM quiz_results WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


@router.message(F.text == "💰 Узнать о доходе")
async def start_quiz(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    # Проверяем, проходил ли уже квиз
    if has_completed_quiz(user_id):
        # Показываем персонализированную информацию о доходе
        
        
        birth_date = user.get('birth_date', '01.01.2000') if user else '01.01.2000'
        gen_info = get_generation_info(birth_date)
        
        short_text = f"""
💰 <b>Возможность дополнительного дохода</b>

🌟 <b>{user['fio']}</b>, вы можете {gen_info['desc']}\n\n

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

В компании Global Trend вы можете получать доход от рекомендации продукции и развития команды.

Нажмите "Развернуть" для подробной информации о системе доходов.
"""
        await message.answer(
            short_text,
            reply_markup=income_info_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await state.set_state(Quiz.q1)
    await send_question(message, state, 1)


async def send_question(message: Message, state: FSMContext, q_num: int):
    """Отправляет вопрос"""
    question = QUESTIONS[q_num]
    
    keyboard = []
    for text, score in question["options"]:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"quiz_{q_num}_{score}")])
    
    await message.answer(
        question["text"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data.startswith("quiz_"))
async def answer_question(callback: CallbackQuery, state: FSMContext):
    print(f"🔴🔴🔴 quiz обработчик СРАБОТАЛ! data={callback.data}")
    parts = callback.data.split("_")
    q_num = int(parts[1])
    score = int(parts[2])
    
    # Сохраняем ответ
    data = await state.get_data()
    answers = data.get("answers", {})
    answers[q_num] = score
    await state.update_data(answers=answers)
    
    # Переход к следующему вопросу
    if q_num < 6:
        await send_question(callback.message, state, q_num + 1)
    else:
        # Квиз завершён
        await finish_quiz(callback, state)
    
    await callback.answer()


async def finish_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})
    
    total_score = sum(answers.values())
    result = get_result_by_score(total_score)
    
    save_quiz_result(callback.from_user.id, answers, total_score, result["level"])
    
    from database import get_user, get_sponsor
    user = get_user(callback.from_user.id)
    
    # Текст результата квиза
    quiz_text = (
        f"📊 **Результат диагностики**\n\n"
        f"🔹 {result['title']}\n\n"
        f"{result['message']}\n\n"
        f"📈 **Ваш потенциал:** {total_score} из 30 баллов\n\n"
        f"👇 Ниже представлена информация о доходах:"
    )
    
    await callback.message.edit_text(quiz_text, parse_mode="Markdown")
    
    # Отправляем персонализированную информацию о доходе
    from handlers.income import income_info_keyboard, get_generation_info
    from database import get_user
    
    user = get_user(callback.from_user.id)
    birth_date = user.get('birth_date', '01.01.2000') if user else '01.01.2000'
    gen_info = get_generation_info(birth_date)
    
    short_text = f"""
💰 <b>Возможность дополнительного дохода</b>

🌟 <b>{user['fio']}</b>, вы можете {gen_info['desc']}\n\n

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

В компании Global Trend вы можете получать доход от рекомендации продукции и развития команды.

Нажмите "Развернуть" для подробной информации о системе доходов.
"""
    
    await callback.message.answer(
        short_text,
        reply_markup=income_info_keyboard(),
        parse_mode="HTML"
    )
    
    # Отправляем результат наставнику
    sponsor = get_sponsor(callback.from_user.id)
    if sponsor and sponsor.get("sponsor_id"):
        try:
            from aiogram import Bot
            from config import MAIN_BOT_TOKEN
            
            bot = Bot(token=MAIN_BOT_TOKEN)
            
            answers_text = "\n".join([f"Вопрос {k}: {v} баллов" for k, v in answers.items()])
            
            mentor_text = (
                f"📋 **Результаты квиза пользователя**\n\n"
                f"👤 **Пользователь:** {user['fio']}\n"
                f"📞 **Телефон:** {user['phone']}\n"
                f"🏙️ **Город:** {user['city']}\n"
                f"📊 **Результат:** {result['title']}\n"
                f"🎯 **Баллы:** {total_score} из 30\n\n"
                f"📝 **Ответы:**\n{answers_text}\n\n"
                f"🚀 **Рекомендация:** {result['message']}"
            )
            
            await bot.send_message(
                sponsor["sponsor_id"],
                mentor_text,
                parse_mode="Markdown"
            )
            await bot.session.close()
        except Exception as e:
            print(f"Ошибка отправки результатов наставнику: {e}")
    
    await state.clear()

@router.callback_query(lambda c: c.data == "how_to_refer")
async def how_to_refer(callback: CallbackQuery):
    from database import get_user, get_referrals_count
    
    user = get_user(callback.from_user.id)
    
    text = """
🤝 <b>Как рекомендовать продукцию</b>

1️⃣ <b>Поделитесь своей ссылкой</b>
Нажмите на кнопку "🔗 Моя ссылка" в главном меню и отправьте её друзьям.

2️⃣ <b>Расскажите о продукции</b>
Поделитесь личным опытом использования продуктов Global Trend.

3️⃣ <b>Помогите зарегистрироваться</b>
Когда человек переходит по вашей ссылке, регистрируется и приобретает продукт в компании, он становится вашим партнёром.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>Ваша статистика</b>
"""
    
    if user:
        referrals_count = get_referrals_count(callback.from_user.id)
        text += f"👥 Приглашено людей: {referrals_count}\n"
        
        if referrals_count >= 2:
            text += "✅ <b>Условие для бонусов выполнено!</b>"
        else:
            need = 2 - referrals_count
            text += f"⚠️ Для стабильных бонусов нужно пригласить ещё {need} человек(а)."
    else:
        text += "Зарегистрируйтесь, чтобы видеть свою статистику."
    
    text += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Совет:</b> Стабильный доход приходит, когда у вас есть минимум 2 активных партнёра.

❓ <b>Если у вас нет наставника</b> — напишите администрации, и вам его назначат.
"""
    
    await callback.message.answer(
        text,
        parse_mode="HTML"
    )
    await callback.answer()    

async def cancel_quiz(message: Message, state: FSMContext):
    """Отмена квиза (если пользователь передумал)"""
    await state.clear()
    await message.answer(
        "❌ Квиз отменён.\n\n"
        "Вы всегда можете пройти его позже через кнопку «💰 Узнать о доходе».",
        reply_markup=products_menu_keyboard
    )